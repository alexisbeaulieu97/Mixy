// internal/tui/prompter.go
package tui

import (
	"errors"
	"fmt"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	// No slog needed here unless debugging TUI internals
)

// ErrUserCancelled is returned when the user quits the TUI prompt.
// Keep this specific error exported if needed by callers like the resolver.
var ErrUserCancelled = errors.New("user cancelled input")

// --- Styles remain the same ---
var (
	labelStyle    = lipgloss.NewStyle().Padding(0, 1)
	focusedStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("205")) // Magenta
	helpStyle     = lipgloss.NewStyle().Foreground(lipgloss.Color("241")) // Grey
	errorStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("196")) // Red
	quittingStyle = lipgloss.NewStyle().Bold(true)
)

// Model represents the state of the multi-input prompt.
type Model struct {
	prompts         []string
	inputs          []textinput.Model
	currentIndex    int
	collectedValues map[string]string
	quitting        bool
	err             error // Store internal errors, including cancellation
}

// NewPrompter initializes the TUI model.
func NewPrompter(variablesToPrompt []string) Model { /* ... no change ... */
	m := Model{
		prompts:         variablesToPrompt,
		inputs:          make([]textinput.Model, len(variablesToPrompt)),
		collectedValues: make(map[string]string, len(variablesToPrompt)),
	}

	var t textinput.Model
	for i := range m.inputs {
		t = textinput.New()
		t.Cursor.Style = focusedStyle
		t.CharLimit = 256

		t.Placeholder = fmt.Sprintf("Enter value for %s...", variablesToPrompt[i])

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
func (m Model) Init() tea.Cmd { /* ... no change ... */
	return textinput.Blink
}

// Update handles messages and updates the model.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) { /* ... no change ... */
	if m.quitting {
		return m, tea.Quit
	}

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			m.err = ErrUserCancelled // Set the specific exported error
			m.quitting = true
			return m, tea.Quit

		case "tab", "shift+tab", "enter", "up", "down":
			s := msg.String()

			if s == "enter" {
				m.collectedValues[m.prompts[m.currentIndex]] = m.inputs[m.currentIndex].Value()
				if m.currentIndex == len(m.inputs)-1 {
					m.quitting = true
					return m, tea.Quit
				}
				m.nextInput()
				return m, textinput.Blink
			}

			if s == "up" || s == "shift+tab" {
				m.prevInput()
			} else {
				m.nextInput()
			}

			cmds := make([]tea.Cmd, len(m.inputs))
			for i := 0; i <= len(m.inputs)-1; i++ {
				if i == m.currentIndex {
					cmds[i] = m.inputs[i].Focus()
					m.inputs[i].PromptStyle = focusedStyle
					m.inputs[i].TextStyle = focusedStyle
					continue
				}
				m.inputs[i].Blur()
				m.inputs[i].PromptStyle = lipgloss.NewStyle()
				m.inputs[i].TextStyle = lipgloss.NewStyle()
			}
			return m, tea.Batch(cmds...)
		}
	}

	cmd := m.updateInputs(msg)
	return m, cmd
}

// updateInputs passes messages to the currently focused input field.
func (m *Model) updateInputs(msg tea.Msg) tea.Cmd { /* ... no change ... */
	cmds := make([]tea.Cmd, len(m.inputs))

	for i := range m.inputs {
		if i == m.currentIndex {
			m.inputs[i], cmds[i] = m.inputs[i].Update(msg)
			break
		}
	}

	return tea.Batch(cmds...)
}

// nextInput moves focus to the next input field.
func (m *Model) nextInput() { /* ... no change ... */
	m.currentIndex = (m.currentIndex + 1) % len(m.inputs)
}

// prevInput moves focus to the previous input field.
func (m *Model) prevInput() { /* ... no change ... */
	m.currentIndex--
	if m.currentIndex < 0 {
		m.currentIndex = len(m.inputs) - 1
	}
}

// View renders the TUI.
func (m Model) View() string { /* ... no change ... */
	if m.quitting {
		// Check the specific error type for cancellation message
		if errors.Is(m.err, ErrUserCancelled) {
			return quittingStyle.Render("Input cancelled.\n")
		}
		// Handle other potential internal TUI errors if they occur
		if m.err != nil {
			return errorStyle.Render(fmt.Sprintf("TUI Error: %v\n", m.err))
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
func RunPrompt(variablesToPrompt []string) (map[string]string, error) { /* ... no change ... */
	if len(variablesToPrompt) == 0 {
		return make(map[string]string), nil
	}

	initialModel := NewPrompter(variablesToPrompt)
	p := tea.NewProgram(initialModel)

	finalModel, err := p.Run()
	if err != nil {
		// This is an error from bubbletea itself (e.g., terminal setup failed)
		return nil, fmt.Errorf("failed to run TUI prompt: %w", err)
	}

	resultModel, ok := finalModel.(Model)
	if !ok {
		return nil, fmt.Errorf("internal error: TUI model has unexpected type %T", finalModel)
	}

	// Check if the model stored an error (like cancellation)
	if resultModel.err != nil {
		return nil, resultModel.err // Propagate internal errors (e.g., ErrUserCancelled)
	}

	return resultModel.collectedValues, nil
}
