import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding database...');

  // Create test users
  const passwordHash = await bcrypt.hash('test123', 10);

  const user1 = await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      email: 'test@example.com',
      name: 'Test User',
      passwordHash,
      githubUsername: 'testuser',
      isActive: true,
    },
  });

  const user2 = await prisma.user.upsert({
    where: { email: 'dev@example.com' },
    update: {},
    create: {
      email: 'dev@example.com',
      name: 'Developer',
      passwordHash,
      githubUsername: 'devuser',
      isActive: true,
    },
  });

  console.log('✅ Users created:', { user1: user1.email, user2: user2.email });

  // Create test project
  const project = await prisma.project.upsert({
    where: { id: '00000000-0000-0000-0000-000000000001' },
    update: {},
    create: {
      id: '00000000-0000-0000-0000-000000000001',
      name: 'Test Project',
      description: 'A test project for development',
      status: 'active',
      tags: ['test', 'development'],
      technologyTags: ['typescript', 'nodejs'],
      resumeContext: {
        last: {
          session_id: null,
          session_summary: 'Initial project setup',
          completed_todos: [],
          updated_elements: [],
          timestamp: new Date().toISOString(),
        },
        now: {
          next_todos: [],
          active_elements: [],
          immediate_goals: ['Setup database', 'Create API'],
        },
        next_blockers: {
          blocked_todos: [],
          waiting_for: [],
          technical_blocks: [],
        },
        constraints: {
          rules: ['TypeScript strict mode', 'No any types'],
          architecture_decisions: [],
          technical_limits: [],
        },
        cursor_instructions: 'Follow TypeScript best practices',
      },
      cursorInstructions: 'Use TypeScript strict mode. Follow RESTful API conventions.',
    },
  });

  console.log('✅ Project created:', project.name);

  // Create user-project relationship
  await prisma.userProject.upsert({
    where: {
      userId_projectId: {
        userId: user1.id,
        projectId: project.id,
      },
    },
    update: {},
    create: {
      userId: user1.id,
      projectId: project.id,
      role: 'owner',
    },
  });

  console.log('✅ User-Project relationship created');

  // Create test feature
  const feature = await prisma.feature.create({
    data: {
      projectId: project.id,
      name: 'Authentication',
      description: 'User authentication and authorization',
      status: 'in_progress',
      totalTodos: 3,
      completedTodos: 1,
      progressPercentage: 33,
      createdBy: user1.id,
    },
  });

  console.log('✅ Feature created:', feature.name);

  // Create test element
  const element = await prisma.projectElement.create({
    data: {
      projectId: project.id,
      type: 'module',
      title: 'Auth Module',
      description: 'Authentication module',
      status: 'in_progress',
    },
  });

  console.log('✅ Element created:', element.title);

  // Create test todos
  const todo1 = await prisma.todo.create({
    data: {
      elementId: element.id,
      featureId: feature.id,
      title: 'Implement login endpoint',
      description: 'Create POST /api/auth/login',
      status: 'done',
      createdBy: user1.id,
      assignedTo: user1.id,
    },
  });

  const todo2 = await prisma.todo.create({
    data: {
      elementId: element.id,
      featureId: feature.id,
      title: 'Implement JWT token generation',
      description: 'Generate access and refresh tokens',
      status: 'in_progress',
      createdBy: user1.id,
      assignedTo: user1.id,
    },
  });

  const todo3 = await prisma.todo.create({
    data: {
      elementId: element.id,
      featureId: feature.id,
      title: 'Add password hashing',
      description: 'Use bcrypt for password hashing',
      status: 'todo',
      createdBy: user1.id,
    },
  });

  console.log('✅ Todos created:', { todo1: todo1.title, todo2: todo2.title, todo3: todo3.title });

  // Link element to feature
  await prisma.featureElement.create({
    data: {
      featureId: feature.id,
      elementId: element.id,
    },
  });

  console.log('✅ Feature-Element link created');

  console.log('🎉 Seeding completed!');
}

main()
  .catch((e) => {
    console.error('❌ Seeding failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
