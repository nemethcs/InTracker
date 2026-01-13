import { Badge } from '@/components/ui/badge'
import { ChevronRight, ChevronDown, Folder, Package, Component, CheckSquare } from 'lucide-react'
import { useState } from 'react'
import type { Element } from '@/services/elementService'

interface ElementTreeProps {
  elements: Element[]
  onElementClick?: (element: Element) => void
}

const typeIcons = {
  milestone: CheckSquare,
  module: Folder,
  component: Component,
  task: Package,
}

const typeColors = {
  milestone: 'text-accent',
  module: 'text-primary',
  component: 'text-green-600 dark:text-green-400',
  task: 'text-yellow-600 dark:text-yellow-400',
}

export function ElementTree({ 
  elements, 
  onElementClick,
  depth = 0 
}: ElementTreeProps & { depth?: number }) {
  if (!elements || elements.length === 0) {
    return null
  }

  return (
    <div className="space-y-0.5">
      {elements.map((element) => (
        <ElementNode
          key={element.id}
          element={element}
          onElementClick={onElementClick}
          depth={depth}
        />
      ))}
    </div>
  )
}

function ElementNode({ 
  element, 
  onElementClick,
  depth = 0 
}: { 
  element: Element
  onElementClick?: (element: Element) => void
  depth?: number
}) {
  // Default to collapsed (false) instead of expanded (true)
  const [isExpanded, setIsExpanded] = useState(false)
  const hasChildren = element.children && element.children.length > 0
  const Icon = typeIcons[element.type] || Folder
  const typeColor = typeColors[element.type] || 'text-muted-foreground'

  return (
    <div className="select-none">
      <div
        className="flex items-center gap-2 p-2.5 rounded-md hover:bg-accent/50 cursor-pointer transition-colors group border-b border-border/50"
        onClick={() => onElementClick?.(element)}
        style={{ paddingLeft: `${depth * 1.5 + 0.5}rem` }}
      >
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
            className="p-1 hover:bg-accent rounded transition-colors flex-shrink-0"
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        ) : (
          <div className="w-6 flex items-center justify-center flex-shrink-0">
            {depth > 0 && (
              <div className="w-0.5 h-4 bg-border/50" />
            )}
          </div>
        )}
        <Icon className={`h-4 w-4 ${typeColor} flex-shrink-0`} />
        <span className="flex-1 text-sm font-medium truncate">{element.title}</span>
        {/* Statistics */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-shrink-0">
          {element.todos_count !== undefined && element.todos_count > 0 && (
            <span 
              className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-muted/50" 
              title={`${element.todos_done_count || 0}/${element.todos_count} todos done`}
            >
              <CheckSquare className="h-3 w-3" />
              <span className="font-medium">{element.todos_done_count || 0}/{element.todos_count}</span>
            </span>
          )}
          {element.features_count !== undefined && element.features_count > 0 && (
            <span 
              className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-muted/50 cursor-help" 
              title={element.linked_features ? `Features: ${element.linked_features.join(', ')}` : `${element.features_count} features`}
            >
              <Package className="h-3 w-3" />
              <span className="font-medium">{element.features_count}</span>
            </span>
          )}
        </div>
        <Badge
          variant={
            element.status === 'done' ? 'default' :
            element.status === 'tested' ? 'secondary' :
            element.status === 'in_progress' ? 'secondary' : 'outline'
          }
          className="text-xs capitalize flex-shrink-0 min-w-[80px] justify-center"
        >
          {element.status.replace('_', ' ')}
        </Badge>
      </div>
      {hasChildren && isExpanded && (
        <div className="relative">
          {depth > 0 && (
            <div 
              className="absolute left-0 top-0 bottom-0 w-px bg-border"
              style={{ left: `${depth * 1.5 + 0.75}rem` }}
            />
          )}
          <ElementTree 
            elements={element.children!} 
            onElementClick={onElementClick}
            depth={depth + 1}
          />
        </div>
      )}
    </div>
  )
}
