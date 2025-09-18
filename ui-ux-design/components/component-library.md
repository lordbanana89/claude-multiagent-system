# Component Library - Claude Multi-Agent System

## Base Components

### 1. Buttons

#### Primary Button
```html
<button class="btn btn-primary">
  Action Text
</button>
```

Variations:
- **Sizes**: small, medium, large
- **States**: default, hover, active, disabled, loading
- **Icons**: left-icon, right-icon, icon-only

#### Secondary Button
```html
<button class="btn btn-secondary">
  Secondary Action
</button>
```

#### Danger Button
```html
<button class="btn btn-danger">
  Delete
</button>
```

### 2. Form Elements

#### Text Input
```html
<div class="form-group">
  <label class="form-label">Label</label>
  <input type="text" class="form-input" placeholder="Enter text...">
  <span class="form-help">Helper text</span>
</div>
```

#### Select Dropdown
```html
<select class="form-select">
  <option>Option 1</option>
  <option>Option 2</option>
</select>
```

#### Checkbox
```html
<label class="checkbox">
  <input type="checkbox">
  <span class="checkbox-label">Option</span>
</label>
```

#### Radio Group
```html
<div class="radio-group">
  <label class="radio">
    <input type="radio" name="group">
    <span class="radio-label">Option 1</span>
  </label>
</div>
```

### 3. Cards

#### Basic Card
```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Title</h3>
  </div>
  <div class="card-body">
    Content
  </div>
  <div class="card-footer">
    Actions
  </div>
</div>
```

#### Agent Status Card
```html
<div class="agent-card" data-status="online">
  <div class="agent-card-header">
    <div class="agent-icon">🤖</div>
    <div class="agent-name">Backend API</div>
    <div class="agent-status">
      <span class="status-dot status-online"></span>
      Online
    </div>
  </div>
  <div class="agent-card-body">
    <div class="metric">
      <span class="metric-label">CPU</span>
      <span class="metric-value">45%</span>
      <div class="metric-bar">
        <div class="metric-fill" style="width: 45%"></div>
      </div>
    </div>
    <div class="metric">
      <span class="metric-label">Memory</span>
      <span class="metric-value">1.2GB</span>
    </div>
    <div class="metric">
      <span class="metric-label">Tasks</span>
      <span class="metric-value">3 active</span>
    </div>
  </div>
  <div class="agent-card-actions">
    <button class="btn-sm">View</button>
    <button class="btn-sm">Stop</button>
    <button class="btn-sm">Logs</button>
  </div>
</div>
```

### 4. Navigation

#### Sidebar Navigation
```html
<nav class="sidebar">
  <div class="sidebar-header">
    <img class="logo" src="logo.svg">
    <span class="app-name">Claude System</span>
  </div>
  <ul class="nav-menu">
    <li class="nav-item active">
      <a class="nav-link">
        <span class="nav-icon">📊</span>
        <span class="nav-text">Dashboard</span>
      </a>
    </li>
    <li class="nav-item">
      <a class="nav-link">
        <span class="nav-icon">🤖</span>
        <span class="nav-text">Agents</span>
        <span class="nav-badge">5</span>
      </a>
    </li>
  </ul>
</nav>
```

#### Tabs
```html
<div class="tabs">
  <ul class="tab-list">
    <li class="tab-item active">
      <button class="tab-link">Overview</button>
    </li>
    <li class="tab-item">
      <button class="tab-link">Analytics</button>
    </li>
    <li class="tab-item">
      <button class="tab-link">Settings</button>
    </li>
  </ul>
  <div class="tab-content">
    <div class="tab-panel active">Content 1</div>
    <div class="tab-panel">Content 2</div>
    <div class="tab-panel">Content 3</div>
  </div>
</div>
```

### 5. Modals

#### Basic Modal
```html
<div class="modal" data-modal="example">
  <div class="modal-backdrop"></div>
  <div class="modal-content">
    <div class="modal-header">
      <h2 class="modal-title">Modal Title</h2>
      <button class="modal-close">×</button>
    </div>
    <div class="modal-body">
      Content
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Confirm</button>
    </div>
  </div>
</div>
```

### 6. Tables

#### Data Table
```html
<table class="data-table">
  <thead>
    <tr>
      <th>Agent</th>
      <th>Status</th>
      <th>CPU</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Backend API</td>
      <td><span class="badge badge-success">Online</span></td>
      <td>45%</td>
      <td>
        <button class="btn-icon">👁️</button>
        <button class="btn-icon">⚙️</button>
      </td>
    </tr>
  </tbody>
</table>
```

### 7. Notifications

#### Toast Notification
```html
<div class="toast toast-success">
  <div class="toast-icon">✓</div>
  <div class="toast-content">
    <div class="toast-title">Success</div>
    <div class="toast-message">Operation completed</div>
  </div>
  <button class="toast-close">×</button>
</div>
```

#### Alert Banner
```html
<div class="alert alert-warning">
  <div class="alert-icon">⚠️</div>
  <div class="alert-content">
    <strong>Warning:</strong> System maintenance scheduled
  </div>
</div>
```

## Custom Agent Components

### 1. Task Progress Bar
```html
<div class="task-progress">
  <div class="task-header">
    <span class="task-name">Processing Data</span>
    <span class="task-percentage">75%</span>
  </div>
  <div class="progress-bar">
    <div class="progress-fill" style="width: 75%">
      <span class="progress-stripes"></span>
    </div>
  </div>
  <div class="task-meta">
    <span class="task-time">2 min remaining</span>
    <span class="task-agent">Database Agent</span>
  </div>
</div>
```

### 2. Workflow Node
```html
<div class="workflow-node" data-type="agent">
  <div class="node-header">
    <span class="node-icon">🤖</span>
    <span class="node-title">Backend API</span>
  </div>
  <div class="node-ports">
    <div class="port port-input"></div>
    <div class="port port-output"></div>
  </div>
  <div class="node-status">Ready</div>
</div>
```

### 3. Message Thread
```html
<div class="message-thread">
  <div class="message message-received">
    <div class="message-avatar">BA</div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-author">Backend Agent</span>
        <span class="message-time">10:45 AM</span>
      </div>
      <div class="message-text">Task completed successfully</div>
    </div>
  </div>
  <div class="message message-sent">
    <div class="message-content">
      <div class="message-header">
        <span class="message-author">Orchestrator</span>
        <span class="message-time">10:46 AM</span>
      </div>
      <div class="message-text">Great! Proceed to next step</div>
    </div>
    <div class="message-avatar">OR</div>
  </div>
</div>
```

### 4. Performance Gauge
```html
<div class="gauge" data-value="75">
  <svg class="gauge-chart" viewBox="0 0 200 100">
    <path class="gauge-background" d="..." />
    <path class="gauge-fill" d="..." />
  </svg>
  <div class="gauge-center">
    <div class="gauge-value">75%</div>
    <div class="gauge-label">CPU Usage</div>
  </div>
</div>
```

### 5. Terminal Emulator
```html
<div class="terminal">
  <div class="terminal-header">
    <div class="terminal-controls">
      <span class="control control-close"></span>
      <span class="control control-minimize"></span>
      <span class="control control-maximize"></span>
    </div>
    <div class="terminal-title">Backend API - Terminal</div>
  </div>
  <div class="terminal-body">
    <div class="terminal-line">
      <span class="terminal-prompt">$</span>
      <span class="terminal-command">npm run build</span>
    </div>
    <div class="terminal-output">
      Building application...
      ✓ Compiled successfully
    </div>
    <div class="terminal-line active">
      <span class="terminal-prompt">$</span>
      <input class="terminal-input" type="text">
    </div>
  </div>
</div>
```

### 6. Activity Timeline
```html
<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-marker"></div>
    <div class="timeline-content">
      <div class="timeline-header">
        <span class="timeline-title">Task Started</span>
        <span class="timeline-time">10:30 AM</span>
      </div>
      <div class="timeline-body">
        Backend API agent started processing authentication module
      </div>
    </div>
  </div>
  <div class="timeline-item timeline-success">
    <div class="timeline-marker"></div>
    <div class="timeline-content">
      <div class="timeline-header">
        <span class="timeline-title">Task Completed</span>
        <span class="timeline-time">10:45 AM</span>
      </div>
      <div class="timeline-body">
        Successfully implemented JWT authentication
      </div>
    </div>
  </div>
</div>
```

## Utility Classes

### Spacing
- `.m-{0-8}` - Margin (all sides)
- `.mt-{0-8}` - Margin top
- `.mr-{0-8}` - Margin right
- `.mb-{0-8}` - Margin bottom
- `.ml-{0-8}` - Margin left
- `.mx-{0-8}` - Margin horizontal
- `.my-{0-8}` - Margin vertical
- `.p-{0-8}` - Padding (same pattern as margin)

### Display
- `.d-none` - Display none
- `.d-block` - Display block
- `.d-inline` - Display inline
- `.d-flex` - Display flex
- `.d-grid` - Display grid

### Flexbox
- `.flex-row` - Flex direction row
- `.flex-column` - Flex direction column
- `.justify-start` - Justify content start
- `.justify-center` - Justify content center
- `.justify-end` - Justify content end
- `.justify-between` - Justify content space-between
- `.align-start` - Align items start
- `.align-center` - Align items center
- `.align-end` - Align items end

### Text
- `.text-left` - Text align left
- `.text-center` - Text align center
- `.text-right` - Text align right
- `.text-sm` - Small text
- `.text-base` - Base text size
- `.text-lg` - Large text
- `.font-normal` - Normal font weight
- `.font-medium` - Medium font weight
- `.font-bold` - Bold font weight

### Colors
- `.text-primary` - Primary text color
- `.text-success` - Success text color
- `.text-warning` - Warning text color
- `.text-error` - Error text color
- `.text-muted` - Muted text color
- `.bg-{color}` - Background colors

### Responsive
- `.sm:*` - Small screens and up
- `.md:*` - Medium screens and up
- `.lg:*` - Large screens and up
- `.xl:*` - Extra large screens and up