# Django Logging — Practical Exercises

The exercises are arranged in increasing difficulty. Each subsequent one builds on the result of the previous.

---

## Theoretical Foundation

### Why do we need logging?

Imagine: your website is running, and something breaks overnight. Users complain in the morning.
If your code had `print()` statements — you won't see anything, because print writes to the console,
and nobody was watching the console. And the server restarted — the output is gone.

Logging solves this problem. It allows you to:
- Separate messages by **severity levels** (debug, error, critical)
- Direct logs to **different destinations** (file, console, email, external service)
- **Enable/disable** logging without changing code
- Add **context** (time, module, line number)

A simple example — why `print` doesn't cut it:

```python
# Bad — print
def create_order(user, items):
    print(f'Creating order for {user}')        # where does this go? nowhere
    print(f'Items: {items}')                   # can't disable without deleting lines
    # ...
    print('Order created')                     # no timestamp, no severity level

# Good — logging
import logging
logger = logging.getLogger(__name__)

def create_order(user, items):
    logger.info('Creating order for %s', user)       # writes to file, console, wherever we say
    logger.debug('Items: %s', items)                  # visible only during debugging
    # ...
    logger.info('Order created')                      # has timestamp, level, module name
```

---

### Architecture of the `logging` module

Django uses Python's standard `logging` module. It has four components:

```
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐
│  Logger  │───>│  Filter  │───>│  Handler  │───>│  Formatter │
│ (source) │    │ (filter) │    │(where we  │    │(how we     │
│          │    │          │    │   write)  │    │   write)   │
└──────────┘    └──────────┘    └───────────┘    └────────────┘
```

Analogy — a postal system:
- **Logger** — the person writing a letter
- **Filter** — the secretary who decides: send the letter or throw it away
- **Handler** — the postal service (one carries to a mailbox, another sends email, a third dispatches a courier)
- **Formatter** — the envelope with formatting (date stamp, return address, layout)

---

### Logging levels (from lowest to highest)

```
DEBUG    (10)  — details for the developer
INFO     (20)  — confirmation that everything is working
WARNING  (30)  — something unexpected, but work continues
ERROR    (40)  — an error, the function was not completed
CRITICAL (50)  — the system cannot continue working
```

If a logger is set to level `WARNING`, then `DEBUG` and `INFO` messages will be **ignored**.

When to use each — real-life examples:

```python
logger.debug('SQL query: SELECT * FROM users WHERE id=5')        # only for the developer
logger.info('User ivan logged in')                                # all ok, just recording
logger.warning('Login attempt with wrong password for ivan')      # suspicious, but not an error
logger.error('Failed to send email: SMTP timeout')               # something broke
logger.critical('Database unavailable, site is down')            # everything crashed
```

---

### Handlers — where we write logs (in detail)

A Handler is a "recipient" of log messages. A single logger can send messages
to multiple handlers simultaneously. Each handler has its own level — it processes
only messages from that level and above.

#### StreamHandler — console output

The simplest one. Writes to `sys.stderr` (by default) or `sys.stdout`.

```python
# In LOGGING['handlers']:
'console': {
    'class': 'logging.StreamHandler',     # handler class
    'level': 'DEBUG',                     # accepts everything from DEBUG and above
    'formatter': 'simple',                # which formatter to use
},
```

When to use: during development (`runserver`), to see logs right in the terminal.

#### FileHandler — writing to a file

Writes to a file. The file grows indefinitely — in production it's better to use RotatingFileHandler.

```python
'file': {
    'class': 'logging.FileHandler',
    'level': 'WARNING',                    # write only WARNING and above to file
    'filename': 'logs/app.log',            # path to the file
    'formatter': 'verbose',
    'encoding': 'utf-8',                   # so Cyrillic doesn't break
},
```

When to use: to write to disk, so you can review later.

#### RotatingFileHandler — file with size-based rotation

When the file reaches a specified size, it gets renamed to `app.log.1`,
the old `app.log.1` becomes `app.log.2`, and so on. The oldest one gets deleted.

```python
'file_rotating': {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': 'logs/app.log',
    'maxBytes': 1024 * 1024 * 10,    # 10 MB — maximum file size
    'backupCount': 5,                # keep 5 old files (app.log.1 ... app.log.5)
    'formatter': 'verbose',
    'encoding': 'utf-8',
},

# What will be on disk:
#   logs/app.log       ← current (most recent)
#   logs/app.log.1     ← previous
#   logs/app.log.2     ← older still
#   ...
#   logs/app.log.5     ← oldest (next one will be deleted)
```

When to use: in production, so logs don't eat up all disk space.

#### TimedRotatingFileHandler — time-based rotation

Creates a new file every day (or hour, or week).

```python
'file_daily': {
    'class': 'logging.handlers.TimedRotatingFileHandler',
    'filename': 'logs/app.log',
    'when': 'midnight',          # new file every midnight
    'interval': 1,               # every 1 day
    'backupCount': 30,           # keep 30 days
    'formatter': 'verbose',
    'encoding': 'utf-8',
},

# What will be on disk:
#   logs/app.log                 ← today's
#   logs/app.log.2026-01-30      ← yesterday's
#   logs/app.log.2026-01-29      ← day before yesterday's
```

When to use: when it's more convenient to search logs by date.

#### AdminEmailHandler — email to administrators (Django)

Sends an email to the addresses from `settings.ADMINS`. Used for critical errors.

```python
'mail_admins': {
    'class': 'django.utils.log.AdminEmailHandler',
    'level': 'ERROR',                            # only ERROR and CRITICAL
    'filters': ['require_debug_false'],           # only when DEBUG=False
    'include_html': True,                         # HTML version with traceback
},

# Don't forget to configure in settings.py:
# ADMINS = [('Name', 'admin@example.com')]
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# ...
```

When to use: to be notified about critical errors in production.

#### Combining handlers

A single logger can write to multiple destinations at once:

```python
'loggers': {
    'myapp': {
        'handlers': ['console', 'file_rotating', 'mail_admins'],  # to three places at once
        'level': 'DEBUG',
    },
},

# What happens when logger.error('Payment error') is called:
#
#   console (level=DEBUG)          → WILL SHOW (ERROR >= DEBUG)
#   file_rotating (level=WARNING)  → WILL WRITE (ERROR >= WARNING)
#   mail_admins (level=ERROR)      → WILL SEND (ERROR >= ERROR)
#
# And when logger.info('User logged in') is called:
#
#   console (level=DEBUG)          → WILL SHOW (INFO >= DEBUG)
#   file_rotating (level=WARNING)  → NO    (INFO < WARNING)
#   mail_admins (level=ERROR)      → NO    (INFO < ERROR)
```

---

### Formatter and `style` — how we format strings (in detail)

A Formatter defines how each line in the log looks.

#### Three formatting styles

The `'style'` parameter specifies which variable substitution syntax is used.
This is **not** about f-strings in your code — it's about the template format inside `'format'`.

**Style `%` (default)** — the old way using `%s`, `%d`:

```python
'formatters': {
    'old_style': {
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        # style not specified — defaults to '%'
    },
},
# Result: 2026-01-31 12:00:00,123 [ERROR] myapp.views: Something broke
```

**Style `{`** — using `str.format()`, curly braces:

```python
'formatters': {
    'new_style': {
        'format': '{asctime} [{levelname}] {name}: {message}',
        'style': '{',
    },
},
# Result: 2026-01-31 12:00:00,123 [ERROR] myapp.views: Something broke
```

**Style `$`** — using `string.Template`, dollar sign:

```python
'formatters': {
    'template_style': {
        'format': '$asctime [$levelname] $name: $message',
        'style': '$',
    },
},
# Result: 2026-01-31 12:00:00,123 [ERROR] myapp.views: Something broke
```

All three styles produce **the same result**. The difference is only in the template syntax.
In practice, `{` is used most often — it reads more clearly than `%(name)s`.

#### Available variables in the format

| Variable      | What it contains                         | Example value                |
|---------------|------------------------------------------|------------------------------|
| `asctime`     | Date and time                            | `2026-01-31 12:00:00,123`   |
| `levelname`   | Level (text)                             | `ERROR`                      |
| `name`        | Logger name                              | `myapp.views`                |
| `message`     | Message text                             | `Something broke`            |
| `module`      | Module name (filename without .py)       | `views`                      |
| `funcName`    | Function name                            | `create_order`               |
| `lineno`      | Line number                              | `42`                         |
| `pathname`    | Full path to the file                    | `/app/myapp/views.py`        |
| `process`     | Process ID                               | `12345`                      |
| `thread`      | Thread ID                                | `140234567`                  |

Example of a verbose formatter for production:

```python
'verbose': {
    'format': '[{asctime}] {levelname} {name} {module}.{funcName}:{lineno} — {message}',
    'style': '{',
},
# Result: [2026-01-31 12:00:00,123] ERROR myapp.views views.create_order:42 — Payment error
```

---

### Filters — filters (in detail)

A filter is a "checkpoint". It looks at a log record and decides:
pass it through (return `True`) or block it (return `False`).

Filters can be placed in **two locations**:
- **On the logger** — the filter checks the message before it reaches any handlers
- **On the handler** — the filter checks the message only for a specific handler

```
logger.warning('Message')
        │
        ▼
  ┌─────────────┐
  │ Filter on   │──── False → message discarded entirely
  │ logger      │
  └──────┬──────┘
         │ True
         ▼
  ┌──────────────┐     ┌──────────────┐
  │ Handler:     │     │ Handler:     │
  │ console      │     │ file         │
  │              │     │              │
  │ Filter on   │     │ Filter on   │
  │ handler ────│──┐  │ handler ────│──┐
  └──────────────┘  │  └──────────────┘  │
    True → outputs  │    True → writes   │
    False → no      │    False → no      │
                    │                    │
```

#### Built-in Django filters

**RequireDebugTrue** — passes messages only when `DEBUG=True` in settings:

```python
'filters': {
    'require_debug_true': {
        '()': 'django.utils.log.RequireDebugTrue',
    },
},

# Usage: show SQL queries only during development
'handlers': {
    'console_dev': {
        'class': 'logging.StreamHandler',
        'filters': ['require_debug_true'],     # ← handler works only when DEBUG=True
    },
},
```

**RequireDebugFalse** — the opposite, passes only when `DEBUG=False`:

```python
'filters': {
    'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse',
    },
},

# Usage: send emails to admins only in production
'handlers': {
    'mail_admins': {
        'class': 'django.utils.log.AdminEmailHandler',
        'filters': ['require_debug_false'],    # ← don't spam emails during development
    },
},
```

**Why is `'()'` needed?** This is special dictConfig syntax. When you write
`'()': 'some.module.SomeClass'`, Python creates an instance of that class. Without `'()'`
Python would just save the string, not create a filter object.

#### Writing your own filter

Any filter is a class with a `filter(self, record)` method.
`record` is an object containing information about the log entry (text, level, time, module...).

**Example 1 — filter by IP address:**

```python
import logging

class BlockInternalIPFilter(logging.Filter):
    """Don't log requests from internal IPs (monitoring, healthcheck)."""

    INTERNAL_IPS = {'127.0.0.1', '10.0.0.1', '192.168.1.1'}

    def filter(self, record):
        # record.getMessage() returns the ready-made message string
        message = record.getMessage()
        for ip in self.INTERNAL_IPS:
            if ip in message:
                return False      # block
        return True               # pass through
```

**Example 2 — filter "don't log static files":**

```python
class SkipStaticFilter(logging.Filter):
    """Don't log requests to /static/ and /media/."""

    def filter(self, record):
        message = record.getMessage()
        if '/static/' in message or '/media/' in message:
            return False
        return True
```

**Example 3 — filter for hiding passwords:**

```python
import re

class HidePasswordFilter(logging.Filter):
    """Replaces passwords in logs with ****."""

    PASSWORD_PATTERN = re.compile(r'(password["\s:=]+)[^\s,}]+', re.IGNORECASE)

    def filter(self, record):
        # Modify the message, but let it pass through
        record.msg = self.PASSWORD_PATTERN.sub(r'\1****', str(record.msg))
        return True   # True = pass through (but with modified text)
```

**Example 4 — filter with a parameter (duplicate suppression):**

```python
import time

class SuppressDuplicatesFilter(logging.Filter):
    """Suppresses identical messages if they repeat more than once every N seconds."""

    def __init__(self, cooldown=5):
        super().__init__()
        self.cooldown = cooldown           # minimum interval in seconds
        self.last_seen = {}                # dictionary {message: time}

    def filter(self, record):
        message = record.getMessage()
        now = time.time()
        last_time = self.last_seen.get(message, 0)

        if now - last_time < self.cooldown:
            return False                   # too soon, suppress
        self.last_seen[message] = now
        return True
```

#### Registering your custom filter in LOGGING

```python
'filters': {
    # Simple filter (no parameters):
    'skip_static': {
        '()': 'myapp.log_filters.SkipStaticFilter',
    },

    # Filter with a parameter:
    'suppress_duplicates': {
        '()': 'myapp.log_filters.SuppressDuplicatesFilter',
        'cooldown': 10,    # parameter passed to __init__
    },
},
```

#### Multiple filters on a single handler

You can attach multiple filters — the message must pass **all** of them:

```python
'handlers': {
    'file': {
        'class': 'logging.FileHandler',
        'filename': 'logs/app.log',
        'filters': ['require_debug_false', 'skip_static', 'hide_passwords'],
        # The message will reach the file only if:
        # 1. DEBUG=False           (require_debug_false)
        # 2. Not a static request  (skip_static)
        # 3. Passwords are hidden  (hide_passwords modifies the text)
    },
},
```

---

### Propagation — message bubbling (in detail)

This is the most confusing topic in logging. Let's break it down step by step.

#### How the logger tree works

Loggers form a hierarchy through **dots in their names**:

```
root                              ← root (has no name)
├── django                        ← parent for all django.*
│   ├── django.request
│   ├── django.db
│   │   └── django.db.backends    ← child of django.db, grandchild of django
│   └── django.security
└── myapp                         ← parent for all myapp.*
    ├── myapp.views
    └── myapp.models
```

When you write `logging.getLogger('myapp.views')`, Python automatically knows
that the parent is `myapp`, and the grandparent is `root`.

#### What is propagation

**Propagation (bubbling)** — after a logger processes a message with its own handlers,
it passes that same message to its parent. The parent passes it to its parent. And so on up to root.

By default `propagate=True` (bubbling is enabled).

#### Example: propagation enabled (default)

```python
LOGGING = {
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'file':    {'class': 'logging.FileHandler', 'filename': 'app.log'},
    },
    'loggers': {
        'myapp': {
            'handlers': ['file'],          # writes to file
            'level': 'DEBUG',
            'propagate': True,             # ← ENABLED (default)
        },
    },
    'root': {
        'handlers': ['console'],           # writes to console
        'level': 'WARNING',
    },
}
```

What happens when `logger.error('Error')` is called in `myapp.views`:

```
1. Logger 'myapp.views' — no own handlers, propagate=True → go to parent

2. Logger 'myapp' — has handler 'file'
   → WROTE TO FILE
   → propagate=True → go to parent

3. Logger 'root' — has handler 'console'
   → OUTPUT TO CONSOLE

Result: the message appeared in BOTH the file AND the console.
```

#### Example: propagation disabled

```python
'loggers': {
    'myapp': {
        'handlers': ['file'],
        'level': 'DEBUG',
        'propagate': False,               # ← DISABLED
    },
},
```

What happens when `logger.error('Error')` is called in `myapp.views`:

```
1. Logger 'myapp.views' — no own handlers, propagate=True → go to parent

2. Logger 'myapp' — has handler 'file'
   → WROTE TO FILE
   → propagate=False → STOP, go no further

3. root — the message did NOT reach here

Result: the message is only in the file. Nothing in the console.
```
