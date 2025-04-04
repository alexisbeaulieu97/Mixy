// Package core provides error types and handling utilities for Mixy operations.
package core

import (
	"errors"
	"fmt"
	"log/slog"
)

// ErrorType categorizes Mixy errors for better error handling and reporting.
type ErrorType uint8 // Use uint8 since we have a small set of error types

// Error type constants define the possible categories of errors in Mixy.
const (
	ErrorTypeUnknown        ErrorType = iota
	ErrorTypeConfiguration            // Configuration parsing or validation errors
	ErrorTypeValidation               // Input validation errors
	ErrorTypeVariable                 // Variable resolution or substitution errors
	ErrorTypeTemplateLoad             // Template source loading errors
	ErrorTypeTemplateRender           // Template rendering/processing errors
	ErrorTypeTemplateMerge            // Template combination errors
	ErrorTypePlugin                   // Plugin loading or execution errors
	ErrorTypeIO                       // File system or network I/O errors
	ErrorTypeCancelled                // User-initiated cancellation
)

// String implements the Stringer interface for ErrorType.
// This enables better logging and error reporting.
func (e ErrorType) String() string {
	switch e {
	case ErrorTypeUnknown:
		return "unknown error"
	case ErrorTypeConfiguration:
		return "configuration error"
	case ErrorTypeValidation:
		return "validation error"
	case ErrorTypeVariable:
		return "variable resolution error"
	case ErrorTypeTemplateLoad:
		return "template loading error"
	case ErrorTypeTemplateRender:
		return "template rendering error"
	case ErrorTypeTemplateMerge:
		return "template merging error"
	case ErrorTypePlugin:
		return "plugin error"
	case ErrorTypeIO:
		return "input/output error"
	case ErrorTypeCancelled:
		return "operation cancelled"
	default:
		return fmt.Sprintf("unknown error type (%d)", e)
	}
}

// MixyError is the standard error type for Mixy operations.
// It provides structured error information including:
// - Error category/type
// - Human-readable message
// - Underlying cause (if any)
// - Contextual information for debugging
type MixyError struct {
	Type    ErrorType   // Category of the error
	Message string      // Human-readable error description
	Cause   error       // Underlying error that caused this error, if any
	Context []slog.Attr // Additional structured context for debugging
}

// NewError creates a new MixyError with the given details.
// The error type and message are required, while cause and context are optional.
func NewError(etype ErrorType, message string, cause error, context ...slog.Attr) error {
	if message == "" {
		message = "no error message provided"
	}
	return &MixyError{
		Type:    etype,
		Message: message,
		Cause:   cause,
		Context: context,
	}
}

// Error implements the error interface with a format that includes
// the error type, message, and underlying cause if present.
func (e *MixyError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("[%s] %s: %v", e.Type, e.Message, e.Cause)
	}
	return fmt.Sprintf("[%s] %s", e.Type, e.Message)
}

// Unwrap implements the errors.Unwrap interface, enabling use with
// errors.Is and errors.As for error chain inspection.
func (e *MixyError) Unwrap() error {
	return e.Cause
}

// LogValue implements slog.LogValuer for structured logging support.
// It creates a structured log entry containing all error details.
func (e *MixyError) LogValue() slog.Value {
	// Start with required fields
	attrs := []slog.Attr{
		slog.String("type", e.Type.String()),
		slog.String("msg", e.Message),
	}

	// Add cause information if present
	if e.Cause != nil {
		attrs = append(attrs, slog.String("cause", e.Cause.Error()))

		// If cause is another MixyError, include its context
		var causeMixy *MixyError
		if errors.As(e.Cause, &causeMixy) {
			attrs = append(attrs, slog.Group("cause_context", toAnySlice(causeMixy.Context)...))
		}
	}

	// Add context if present
	if len(e.Context) > 0 {
		attrs = append(attrs, slog.Group("context", toAnySlice(e.Context)...))
	}

	return slog.GroupValue(attrs...)
}

// toAnySlice converts a slice of slog.Attr to a slice of interface{}
// for use with slog.Group.
func toAnySlice(attrs []slog.Attr) []any {
	anys := make([]any, len(attrs))
	for i, attr := range attrs {
		anys[i] = attr
	}
	return anys
}

// Error constructor functions for common error types

// NewConfigurationError creates an error related to configuration issues.
func NewConfigurationError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeConfiguration, msg, cause, ctx...)
}

// NewValidationError creates an error related to validation failures.
func NewValidationError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeValidation, msg, cause, ctx...)
}

// NewVariableError creates an error related to variable resolution.
func NewVariableError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeVariable, msg, cause, ctx...)
}

// NewTemplateLoadError creates an error related to template loading.
func NewTemplateLoadError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeTemplateLoad, msg, cause, ctx...)
}

// NewTemplateRenderError creates an error related to template rendering.
func NewTemplateRenderError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeTemplateRender, msg, cause, ctx...)
}

// NewTemplateMergeError creates an error related to template merging.
func NewTemplateMergeError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeTemplateMerge, msg, cause, ctx...)
}

// NewPluginError creates an error related to plugin operations.
func NewPluginError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypePlugin, msg, cause, ctx...)
}

// NewIOError creates an error related to I/O operations.
func NewIOError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeIO, msg, cause, ctx...)
}

// Pre-defined errors

// ErrCancelled indicates that an operation was cancelled by the user.
// This is a sentinel error that should be used with errors.Is().
var ErrCancelled = NewError(ErrorTypeCancelled, "operation cancelled by user", nil)
