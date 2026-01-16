import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        success:
          "border-transparent bg-primary/20 text-primary dark:bg-primary/30 hover:bg-primary/30 dark:hover:bg-primary/40",
        warning:
          "border-transparent bg-accent/20 text-accent-foreground dark:bg-accent/30 hover:bg-accent/30 dark:hover:bg-accent/40",
        info:
          "border-transparent bg-primary/10 text-primary dark:bg-primary/20 hover:bg-primary/20 dark:hover:bg-primary/30",
        accent:
          "border-transparent bg-accent text-accent-foreground hover:bg-accent/80",
        muted:
          "border-transparent bg-muted text-muted-foreground hover:bg-muted/80",
        outline: "text-foreground hover:bg-accent/50 hover:border-accent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
