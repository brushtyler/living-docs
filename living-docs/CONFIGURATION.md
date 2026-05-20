# Living Docs Configuration Guide

The `living-docs-config.json` file is the central brain of the documentation pipeline. It defines how the toolkit communicates with your application and how it maps source code to live URLs.

## 1. Core Configuration

At its simplest, your config must define the `base_url` where your application is running locally.

```json
{
  "base_url": "http://localhost:3000"
}
```

### Supported Entries

| Key | Type | Description |
| :--- | :--- | :--- |
| `base_url` | `string` | The root URL of your local dev server (e.g., `http://localhost:3000`). |
| `flows` | `object` | Named sequences of actions (e.g., login) that can be reused as prerequisites in recipes. |
| `mappings` | `array` | Regex-based rules to map source file paths to their corresponding web routes. |

---

## 2. Reusable Authentication Flows

If your app requires authentication to view components, define a `login` flow in the `flows` object.

```json
{
  "flows": {
    "login": [
      {"action": "goto", "url": "/login"},
      {"action": "type", "selector": "#user", "text": "admin_user"},
      {"action": "type", "selector": "#pass", "text": "password123"},
      {"action": "click", "selector": "button[type='submit']"},
      {"action": "wait_for_selector", "selector": "aside.sidebar"}
    ]
  }
}
```

*Note: Recipes can reference this flow using `"prerequisites": ["login"]`.*

---

## 3. Route Mappings

Mappings allow the AI to automatically "resolve" a source file (like a `.tsx` component) to a URL. This powers the **Visual Discovery** feature.

```json
{
  "mappings": [
    {
      "description": "Product Components",
      "pattern": "src/components/products/(.*)\\.tsx",
      "urls": ["/products/sample-id", "/admin/inventory"]
    },
    {
      "description": "User Profile",
      "pattern": "src/features/user/ProfileCard\\.tsx",
      "urls": ["/profile/settings"]
    }
  ]
}
```

- **`pattern`**: A regular expression matched against the file path.
- **`urls`**: A list of URLs where this component can be found.

---

## 4. Advanced: Next.js Auto-Resolution

Living Docs has built-in support for Next.js folder structures. Even without mappings, it can often resolve:
- `app/dashboard/page.tsx` -> `/dashboard`
- `pages/settings/index.js` -> `/settings`

*If your route is dynamic (e.g., `[id]`), see the [Dynamic Routes](#) section in USAGE.md.*
