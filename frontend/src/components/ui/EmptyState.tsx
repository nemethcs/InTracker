import { ReactNode } from 'react'
import { Button } from './button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardHeader className="text-center">
        {icon && <div className="mx-auto mb-4">{icon}</div>}
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      {action && (
        <CardFooter className="justify-center">
          <Button onClick={action.onClick}>{action.label}</Button>
        </CardFooter>
      )}
    </Card>
  )
}
