import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// Assuming you want to use Tailwind's base styles
import './styles/globals.css'

// Prevent TypeScript error for lacking root element
const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Failed to find the root element')

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)