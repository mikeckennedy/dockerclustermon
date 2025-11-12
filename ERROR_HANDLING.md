# SSH Connection Error Handling

## Overview

The application now has robust error handling for SSH connection failures, including network outages, connection timeouts, and other SSH-related issues.

## Error Handling Flow

### 1. Connection Creation (`get_ssh_client()`)

When creating or checking an SSH connection:

```python
def get_ssh_client(username: str, host: str, ssh_config: bool) -> Optional[paramiko.SSHClient]:
    # Check if existing connection is alive
    if ssh_client is not None:
        try:
            transport = ssh_client.get_transport()
            if transport and transport.is_active():
                return ssh_client  # Reuse connection
        except Exception:
            # Connection is dead, clean it up
            ssh_client.close()
            ssh_client = None
    
    # Create new connection
    try:
        # ... connection logic ...
        return ssh_client
    except Exception as e:
        if DEBUG_MODE:
            console.print(f'Failed to create SSH connection: {e}')
        return None  # Connection failed
```

**Behavior:**
- ✅ Returns existing connection if still alive
- ✅ Detects dead connections and cleans them up
- ✅ Returns `None` if connection fails (network down, auth failure, etc.)
- ✅ Shows detailed error in debug mode

### 2. Command Execution (`run_command_with_debug()`)

When executing commands:

```python
def run_command_with_debug(..., ssh_client, no_ssh):
    # Detect when SSH is required but connection failed
    if not no_ssh and ssh_client is None:
        raise ConnectionError('SSH connection failed - unable to connect to remote host')
    
    # Execute command via SSH or locally
    if ssh_client is not None:
        return run_ssh_command(ssh_client, command, timeout)
    else:
        return subprocess.run(...)  # Local execution
```

**Behavior:**
- ✅ Raises `ConnectionError` if SSH is needed but connection is `None`
- ✅ Prevents confusing errors from trying to run remote commands locally
- ✅ Clear error message for troubleshooting

### 3. Display Layer (`build_table()`)

When building the display table:

```python
def build_table(...):
    try:
        run_update(...)
        reduced, total, total_cpu, total_mem, used = process_results()
    except TimeoutExpired:
        # Show timeout error and retry
        table.add_row('Error', 'Server did not respond after X seconds. Retrying', ...)
        return table
    except ConnectionError as ce:
        # Show connection error and retry
        table.add_row('Error', f'SSH connection failed: {ce}. Retrying', ...)
        return table
    except CalledProcessError as cpe:
        # Command execution failed
        print(f'Error: {cpe}')
        return None
    except Exception as x:
        # Catch-all for other errors
        table.add_row('Error', str(x), ...)
        return table
```

**Behavior:**
- ✅ Catches `ConnectionError` and displays user-friendly message
- ✅ Continues the monitoring loop (keeps retrying)
- ✅ Shows timestamp of when error occurred
- ✅ Different handling for different error types

## Behavior in Different Scenarios

### Scenario 1: Network Goes Down (No Debug Mode)

**What happens:**
1. `get_ssh_client()` tries to create connection → fails → returns `None`
2. `run_command_with_debug()` detects `ssh_client is None` → raises `ConnectionError`
3. `build_table()` catches `ConnectionError` → displays in table:
   ```
   Error | SSH connection failed on Nov 12, 2025 @ 10:45:23 AM: SSH connection failed - unable to connect to remote host. Retrying
   ```
4. App waits 1 second, then retries on next refresh
5. When network comes back, connection is re-established automatically

**User experience:**
- ✅ No crash or exit
- ✅ Clear error message
- ✅ Automatic retry
- ✅ Automatic recovery when network returns

### Scenario 2: Connection Dies Mid-Command (No Debug Mode)

**What happens:**
1. Existing connection is passed to `run_ssh_command()`
2. Paramiko detects connection is dead during `exec_command()` → raises `paramiko.SSHException`
3. `run_ssh_command()` catches it → raises `CalledProcessError`
4. Command function (`run_ps_command`, etc.) catches it → sets `results['error']`
5. `run_update()` detects `results['error']` → re-raises it
6. `build_table()` catches the error → displays in table
7. Next refresh cycle: `get_ssh_client()` detects dead connection → creates new one

**User experience:**
- ✅ Error displayed in table
- ✅ Automatic reconnection on next cycle
- ✅ Monitoring continues

### Scenario 3: Intermittent Connection (No Debug Mode)

**What happens:**
1. First attempt: Connection fails → shows error in table
2. Second attempt: Still fails → shows error again
3. Third attempt: Succeeds → resumes normal monitoring
4. Each failed attempt: waits 1 second before retry

**User experience:**
- ✅ Non-blocking errors
- ✅ Clear feedback on connection status
- ✅ No manual intervention needed

### Scenario 4: Any Error in Debug Mode

**What happens:**
1. Error occurs at any level
2. Exception is caught and **re-raised** in debug mode
3. Full exception with stack trace shown
4. Application exits with error code

**User experience:**
- ✅ Full debugging information
- ✅ See exactly where/why it failed
- ✅ Useful for troubleshooting

## Connection Lifecycle with Error Handling

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Start                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  get_ssh_client()    │
            └──────────┬───────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
    Connection OK              Connection Failed
         │                           │
         │                           ▼
         │                  Return None
         │                           │
         ▼                           ▼
  Pass client to         Raise ConnectionError
  command functions              │
         │                       │
         ▼                       ▼
  Execute commands       Display in table
         │                   "SSH connection
         │                   failed. Retrying"
         │                           │
         ▼                           ▼
  Show results            Wait 1 second
         │                           │
         └───────────────┬───────────┘
                         │
                         ▼
                   Next Refresh
                   (retry connection)
```

## Key Benefits

1. **Graceful Degradation**: Errors don't crash the app
2. **Auto-Recovery**: Automatically reconnects when network returns
3. **Clear Feedback**: User knows exactly what's happening
4. **Debug Support**: Detailed info when needed with `--debug` flag
5. **No Manual Intervention**: Just wait for network to return

## Testing Scenarios

To test error handling:

### Test 1: Disconnect Network
```bash
# Start monitoring
ds user@host

# In another terminal, disable network
sudo ifconfig en0 down

# Observe: Error message in table, automatic retry
# Re-enable network
sudo ifconfig en0 up

# Observe: Automatic reconnection and resumption
```

### Test 2: Firewall Block SSH
```bash
# Start monitoring
ds user@host

# Block SSH port
sudo pfctl -e
sudo pfctl -a my_block -f - <<EOF
block drop proto tcp from any to any port 22
EOF

# Observe: Connection error, automatic retry
# Unblock
sudo pfctl -a my_block -F all

# Observe: Automatic reconnection
```

### Test 3: Server Down
```bash
# Start monitoring
ds user@host

# Shut down remote server
ssh user@host "sudo shutdown -h now"

# Observe: Connection errors with retry messages
# Start server again
# Observe: Automatic reconnection when server returns
```

## Debug Mode Differences

| Scenario | Normal Mode | Debug Mode |
|----------|-------------|------------|
| Connection fails | Show error in table, retry | Show full exception, exit |
| Command fails | Show error in table, retry | Show full exception, exit |
| Timeout occurs | Show timeout message, retry | Show full exception, exit |
| Network drops | Show connection error, retry | Show full exception, exit |

**When to use debug mode:**
- Troubleshooting connection issues
- Diagnosing why commands are failing
- Getting full error details for bug reports
- Development and testing

**When to use normal mode:**
- Production monitoring
- Long-running sessions
- Unstable networks (want auto-retry)
- Unattended operation

