// internal/core/errors.go
package core

import (
	"errors"
	"fmt"
	"log/slog" // Import slog
)

// ErrorType categorizes Mixy errors.
type ErrorType uint

const (
	ErrorTypeUnknown        ErrorType = iota // unknown error
	ErrorTypeConfiguration                   // configuration error
	ErrorTypeValidation                      // validation error
	ErrorTypeVariable                        // variable resolution error
	ErrorTypeTemplateLoad                    // template loading error
	ErrorTypeTemplateRender                  // template rendering error
	ErrorTypeTemplateMerge                   // template merging error
	ErrorTypePlugin                          // plugin error
	ErrorTypeIO                              // input/output error
	ErrorTypeCancelled                       // operation cancelled
)

// String returns the string representation of ErrorType
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
		return "unknown error type"
	}
}

// MixyError is our standard structured error type.
type MixyError struct {
	Type    ErrorType
	Message string
	Cause   error
	Context []slog.Attr // Use slog.Attr for structured context
}

// NewError creates a new MixyError.
func NewError(etype ErrorType, message string, cause error, context ...slog.Attr) *MixyError {
	return &MixyError{
		Type:    etype,
		Message: message,
		Cause:   cause,
		Context: context,
	}
}

// Error implements the standard error interface.
func (e *MixyError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("[%s] %s: %v", e.Type, e.Message, e.Cause)
	}
	return fmt.Sprintf("[%s] %s", e.Type, e.Message)
}

// Unwrap returns the underlying cause for error chaining (fmt.Errorf %w, errors.Is/As).
func (e *MixyError) Unwrap() error {
	return e.Cause
}

// LogValue implements slog.LogValuer for structured logging of the error.
func (e *MixyError) LogValue() slog.Value {
	attrs := []slog.Attr{
		slog.String("msg", e.Message),
		slog.String("type", e.Type.String()),
	}
	if e.Cause != nil {
		// Log the cause as a nested error string for now.
		// More sophisticated logging could log the cause's details recursively.
		attrs = append(attrs, slog.String("cause", e.Cause.Error()))
		// If the cause is also a MixyError, embed its context
		var causeMixy *MixyError
		if errors.As(e.Cause, &causeMixy) {
			attrs = append(attrs, slog.Group("cause_context", toAnySlice(causeMixy.Context)...))
		}
	}
	if len(e.Context) > 0 {
		attrs = append(attrs, slog.Group("context", toAnySlice(e.Context)...))
	}

	return slog.GroupValue(attrs...)
}

// Helper to convert []slog.Attr to []any for slog.Group
func toAnySlice(attrs []slog.Attr) []any {
	anys := make([]any, len(attrs))
	for i, attr := range attrs {
		anys[i] = attr
	}
	return anys
}

// Helper function to create common error types easily
func NewConfigurationError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeConfiguration, msg, cause, ctx...)
}

func NewValidationError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeValidation, msg, cause, ctx...)
}

func NewTemplateLoadError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeTemplateLoad, msg, cause, ctx...)
}

func NewTemplateRenderError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeTemplateRender, msg, cause, ctx...)
}

func NewPluginError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypePlugin, msg, cause, ctx...)
}

func NewIOError(msg string, cause error, ctx ...slog.Attr) error {
	return NewError(ErrorTypeIO, msg, cause, ctx...)
}

// Error specific to user cancellation (avoids exporting tui.ErrUserCancelled everywhere)
var ErrCancelled = NewError(ErrorTypeCancelled, "operation cancelled by user", nil)
