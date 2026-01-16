/**
 * Type definitions for Pydantic validation errors
 */

export interface PydanticValidationError {
  loc: (string | number)[]
  msg: string
  type: string
  input?: unknown
}

export type PydanticErrorDetail = string | PydanticValidationError[] | Record<string, unknown>
