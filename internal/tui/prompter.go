// internal/tui/prompter.go
package tui

import (
	"errors"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// ErrUserCancelled is returned when the user quits the TUI prompt.
var ErrUserCancelled = errors.New("user cancelled input")

var (
	labelStyle    = lipgloss.NewStyle().Padding(0, 1)
	focusedStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("205")) // Magenta
	helpStyle     = lipgloss.NewStyle().Foreground(lipgloss.Color("241")) // Grey
	errorStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("196")) // Red
	quittingStyle = lipgloss.NewStyle().Bold(true)
)

// Model represents the state of the multi-input prompt.
type Model struct {
	prompts         []string          // The variable names to prompt for
	inputs          []textinput.Model // Input fields
	currentIndex    int               // Index of the currently focused input
	collectedValues map[string]string // Values entered by the user
	quitting        bool              // Flag to indicate the user wants to quit
	err             error             // Stores errors (e.g., cancellation)
}

// NewPrompter initializes the TUI model.
func NewPrompter(variablesToPrompt []string) Model {
	m := Model{
		prompts:         variablesToPrompt,
		inputs:          make([]textinput.Model, len(variablesToPrompt)),
		collectedValues: make(map[string]string, len(variablesToPrompt)),
	}

	var t textinput.Model
	for i := range m.inputs {
		t = textinput.New()
		t.Cursor.Style = focusedStyle
		t.CharLimit = 256 // Or make configurable

		// Set placeholder based on variable name
		t.Placeholder = fmt.Sprintf("Enter value for %s...", variablesToPrompt[i])

		// Set initial focus
		if i == 0 {
			t.Focus()
			t.PromptStyle = focusedStyle
			t.TextStyle = focusedStyle
		}

		m.inputs[i] = t
	}

	return m
}

// Init initializes the bubbletea program.
func (m Model) Init() tea.Cmd {
	// Start the blinking cursor
	return textinput.Blink
}

// Update handles messages and updates the model.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// If quitting, don't process further messages
	if m.quitting {
		return m, tea.Quit
	}

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			m.err = ErrUserCancelled
			m.quitting = true
			return m, tea.Quit

		case "tab", "shift+tab", "enter", "up", "down":
			s := msg.String()

			// Did the user press enter?
			if s == "enter" {
				// Store the current value
				m.collectedValues[m.prompts[m.currentIndex]] = m.inputs[m.currentIndex].Value()
				// Move to the next input or quit if it's the last one
				if m.currentIndex == len(m.inputs)-1 {
					m.quitting = true
					return m, tea.Quit
				}
				m.nextInput()
				return m, textinput.Blink // Restart blink on the new input
			}

			// Cycle through inputs
			if s == "up" || s == "shift+tab" {
				m.prevInput()
			} else {
				m.nextInput()
			}

			// Update focus styles and manage cursor blinking
			cmds := make([]tea.Cmd, len(m.inputs))
			for i := 0; i <= len(m.inputs)-1; i++ {
				if i == m.currentIndex {
					// Set focused state
					cmds[i] = m.inputs[i].Focus()
					m.inputs[i].PromptStyle = focusedStyle
					m.inputs[i].TextStyle = focusedStyle
					continue
				}
				// Remove focused state
				m.inputs[i].Blur()
				m.inputs[i].PromptStyle = lipgloss.NewStyle()
				m.inputs[i].TextStyle = lipgloss.NewStyle()
			}
			return m, tea.Batch(cmds...) // Batch commands for focus and blink
		}
	}

	// Handle character input and blinking for the focused input
	cmd := m.updateInputs(msg)
	return m, cmd
}

// updateInputs passes messages to the currently focused input field.
func (m *Model) updateInputs(msg tea.Msg) tea.Cmd {
	cmds := make([]tea.Cmd, len(m.inputs))

	// Only update the focused input
	for i := range m.inputs {
		if i == m.currentIndex {
			m.inputs[i], cmds[i] = m.inputs[i].Update(msg)
			break // Stop after updating the focused one
		}
	}

	return tea.Batch(cmds...)
}

// nextInput moves focus to the next input field.
func (m *Model) nextInput() {
	m.currentIndex = (m.currentIndex + 1) % len(m.inputs)
}

// prevInput moves focus to the previous input field.
func (m *Model) prevInput() {
	m.currentIndex--
	// Wrap around
	if m.currentIndex < 0 {
		m.currentIndex = len(m.inputs) - 1
	}
}

// View renders the TUI.
func (m Model) View() string {
	if m.quitting {
		if m.err != nil {
			return errorStyle.Render(fmt.Sprintf("Input cancelled: %v\n", m.err))
		}
		return quittingStyle.Render("Input collected. Processing...\n")
	}

	var b strings.Builder

	b.WriteString("Please provide values for the following mandatory variables:\n\n")

	for i := range m.inputs {
		b.WriteString(labelStyle.Render(m.prompts[i] + ":"))
		b.WriteString(m.inputs[i].View())
		if i < len(m.inputs)-1 {
			b.WriteRune('\n')
		}
	}

	b.WriteString("\n\n")
	b.WriteString(helpStyle.Render("Enter: next/submit | Tab/Down: next | Shift+Tab/Up: previous | Esc/Ctrl+C: quit"))

	return b.String()
}

// RunPrompt executes the Bubble Tea program and returns the collected values or an error.
func RunPrompt(variablesToPrompt []string) (map[string]string, error) {
	if len(variablesToPrompt) == 0 {
		return make(map[string]string), nil // Nothing to prompt for
	}

	initialModel := NewPrompter(variablesToPrompt)
	p := tea.NewProgram(initialModel)

	// Run returns the final model state
	finalModel, err := p.Run()
	if err != nil {
		return nil, fmt.Errorf("failed to run TUI prompt: %w", err)
	}

	// Cast the final model back to our struct type
	resultModel, ok := finalModel.(Model)
	if !ok {
		// This shouldn't happen if p.Run() succeeds without error
		return nil, fmt.Errorf("internal error: TUI model has unexpected type %T", finalModel)
	}

	// Check if the user cancelled within the TUI
	if resultModel.err != nil {
		return nil, resultModel.err // Propagate ErrUserCancelled
	}

	// Return the collected values
	return resultModel.collectedValues, nil
}
