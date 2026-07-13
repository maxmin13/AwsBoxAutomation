import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import awsAccountSetup from '../../../docs/AWS_ACCOUNT_SETUP.md?raw'

const DOCS = [
  { id: 'aws-account-setup', title: 'AWS Account Setup', content: awsAccountSetup },
]

export default function DocsPage() {
  const [selected, setSelected] = useState(DOCS[0].id)
  const doc = DOCS.find(d => d.id === selected)!

  return (
    <div className="flex gap-6 h-full">
      <nav className="w-48 shrink-0">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Docs</p>
        <ul className="space-y-1">
          {DOCS.map(d => (
            <li key={d.id}>
              <button
                onClick={() => setSelected(d.id)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                  selected === d.id
                    ? 'bg-zinc-700 text-zinc-100'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                }`}
              >
                {d.title}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="flex-1 overflow-y-auto">
        <article className="prose prose-invert prose-sm max-w-2xl">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children }) => (
                <a
                  href={href}
                  onClick={e => { e.preventDefault(); if (href) window.electronAPI.openExternal(href) }}
                  className="cursor-pointer"
                >
                  {children}
                </a>
              ),
            }}
          >
            {doc.content}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  )
}
