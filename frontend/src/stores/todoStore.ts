import { create } from 'zustand'
import { todoService, type Todo, type TodoCreate, type TodoUpdate } from '@/services/todoService'
import { signalrService } from '@/services/signalrService'
import type { TodoUpdateData } from '@/types/signalr'

interface TodoState {
  todos: Todo[]
  isLoading: boolean
  error: string | null
  fetchTodos: (featureId?: string, elementId?: string, projectId?: string) => Promise<void>
  fetchTodo: (id: string) => Promise<Todo>
  createTodo: (data: TodoCreate) => Promise<Todo>
  updateTodo: (id: string, data: TodoUpdate) => Promise<void>
  updateTodoStatus: (id: string, status: Todo['status'], version: number) => Promise<void>
  deleteTodo: (id: string) => Promise<void>
}

export const useTodoStore = create<TodoState>((set, get) => {
  // Subscribe to SignalR todo updates
  signalrService.on('todoUpdated', (data: TodoUpdateData) => {
    const { todos } = get()
    const todoIndex = todos.findIndex(t => t.id === data.todoId)
    
    if (todoIndex >= 0) {
      // Update existing todo with changes
      const updatedTodos = [...todos]
      updatedTodos[todoIndex] = {
        ...updatedTodos[todoIndex],
        ...data.changes,
        // If status changed, update version
        version: data.changes.status ? (updatedTodos[todoIndex].version || 0) + 1 : updatedTodos[todoIndex].version
      }
      set({ todos: updatedTodos })
    } else {
      // Todo not in current list, fetch it if needed
      // This handles cases where a todo is created/updated in another view
      todoService.getTodo(data.todoId).then(todo => {
        const { todos } = get()
        if (!todos.find(t => t.id === todo.id)) {
          set({ todos: [...todos, todo] })
        }
      }).catch(() => {
        // Todo might not exist or we don't have access, ignore
      })
    }
  })

  return {
    todos: [],
    isLoading: false,
    error: null,

  fetchTodos: async (featureId?: string, elementId?: string, projectId?: string) => {
    set({ isLoading: true, error: null })
    try {
      const todos = await todoService.listTodos(featureId, elementId, projectId)
      set({ todos, isLoading: false })
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch todos', isLoading: false })
    }
  },

  fetchTodo: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const todo = await todoService.getTodo(id)
      set(state => {
        const index = state.todos.findIndex(t => t.id === id)
        if (index >= 0) {
          const todos = [...state.todos]
          todos[index] = todo
          return { todos, isLoading: false }
        }
        return { todos: [...state.todos, todo], isLoading: false }
      })
      return todo
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to fetch todo', isLoading: false })
      throw error
    }
  },

  createTodo: async (data: TodoCreate) => {
    set({ isLoading: true, error: null })
    try {
      const todo = await todoService.createTodo(data)
      set(state => ({ 
        todos: [...state.todos, todo], 
        isLoading: false 
      }))
      return todo
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create todo', isLoading: false })
      throw error
    }
  },

  updateTodo: async (id: string, data: TodoUpdate) => {
    set({ isLoading: true, error: null })
    try {
      const todo = await todoService.updateTodo(id, data)
      set(state => ({
        todos: state.todos.map(t => t.id === id ? todo : t),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update todo', isLoading: false })
      throw error
    }
  },

  updateTodoStatus: async (id: string, status: Todo['status'], version: number) => {
    set({ isLoading: true, error: null })
    try {
      const todo = await todoService.updateTodo(id, { status, expected_version: version })
      set(state => ({
        todos: state.todos.map(t => t.id === id ? todo : t),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update todo status', isLoading: false })
      throw error
    }
  },

  deleteTodo: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await todoService.deleteTodo(id)
      set(state => ({
        todos: state.todos.filter(t => t.id !== id),
        isLoading: false
      }))
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to delete todo', isLoading: false })
      throw error
    }
  },
  }
})
