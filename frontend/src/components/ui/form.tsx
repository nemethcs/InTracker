import * as React from "react"
import { Label } from "./label"
import { Input } from "./input"
import { Textarea } from "./textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select"
import { cn } from "@/lib/utils"
import { AlertCircle } from "lucide-react"

interface FormFieldProps {
  label?: string
  error?: string
  description?: string
  required?: boolean
  children: React.ReactNode
  className?: string
}

export function FormField({
  label,
  error,
  description,
  required,
  children,
  className,
}: FormFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <Label className={cn(required && "after:content-['*'] after:ml-0.5 after:text-destructive")}>
          {label}
        </Label>
      )}
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {children}
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}

// Extended Input with error state
interface FormInputProps extends React.ComponentProps<typeof Input> {
  error?: boolean
}

const FormInput = React.forwardRef<HTMLInputElement, FormInputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <Input
        ref={ref}
        className={cn(
          error && "border-destructive focus-visible:ring-destructive focus-visible:border-destructive",
          className
        )}
        {...props}
      />
    )
  }
)
FormInput.displayName = "FormInput"

// Extended Textarea with error state
interface FormTextareaProps extends React.ComponentProps<typeof Textarea> {
  error?: boolean
}

const FormTextarea = React.forwardRef<HTMLTextAreaElement, FormTextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <Textarea
        ref={ref}
        className={cn(
          error && "border-destructive focus-visible:ring-destructive focus-visible:border-destructive",
          className
        )}
        {...props}
      />
    )
  }
)
FormTextarea.displayName = "FormTextarea"

// Extended Select with error state
interface FormSelectProps extends React.ComponentProps<typeof SelectTrigger> {
  error?: boolean
}

const FormSelect = React.forwardRef<
  React.ElementRef<typeof SelectTrigger>,
  FormSelectProps
>(({ className, error, ...props }, ref) => {
  return (
    <SelectTrigger
      ref={ref}
      className={cn(
        error && "border-destructive focus:ring-destructive focus:border-destructive",
        className
      )}
      {...props}
    />
  )
})
FormSelect.displayName = "FormSelect"

export { FormInput, FormTextarea, FormSelect }
