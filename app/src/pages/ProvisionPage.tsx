import { useState } from 'react'

interface PlaybookDef {
  file:  string
  label: string
  desc:  string
}

interface CategoryDef {
  name:      string
  playbooks: PlaybookDef[]
}

const CATEGORIES: CategoryDef[] = [
  {
    name: 'System',
    playbooks: [
      { file: 'upgrade.yml', label: 'Upgrade', desc: 'yum update and base packages' },
    ],
  },
  {
    name: 'Security',
    playbooks: [
      { file: 'openssl.yml', label: 'OpenSSL', desc: 'OpenSSL 1.1.1u built from source' },
    ],
  },
  {
    name: 'Languages',
    playbooks: [
      { file: 'python.yml', label: 'Python', desc: 'Python 3.11.4 built from source' },
      { file: 'java.yml',   label: 'Java',   desc: 'OpenJDK 18'                      },
    ],
  },
  {
    name: 'Web',
    playbooks: [
      { file: 'nginx.yml',      label: 'Nginx',      desc: 'Nginx with self-signed TLS on 8080 / 8443' },
      { file: 'tomcat.yml',     label: 'Tomcat',     desc: 'Tomcat 10.1.23 with TLS keystore'          },
      { file: 'phpmyadmin.yml', label: 'phpMyAdmin', desc: 'phpMyAdmin on port 8000'                   },
    ],
  },
  {
    name: 'Databases',
    playbooks: [
      { file: 'postgresql.yml', label: 'PostgreSQL', desc: 'PostgreSQL 14' },
      { file: 'mariadb.yml',    label: 'MariaDB',    desc: 'MariaDB 10.5'  },
    ],
  },
  {
    name: 'Containers',
    playbooks: [
      { file: 'docker.yml', label: 'Docker', desc: 'Docker CE 25 and Docker Compose' },
    ],
  },
]

type View = 'categories' | 'playbooks' | 'run'

interface ProvisionPageProps {
  onBack: () => void
}

export default function ProvisionPage({ onBack }: ProvisionPageProps) {
  const [view,             setView]             = useState<View>('categories')
  const [selectedCategory, setSelectedCategory] = useState<CategoryDef | null>(null)
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookDef | null>(null)

  function handleNavBack() {
    if (view === 'run')       { setView('playbooks'); return }
    if (view === 'playbooks') { setView('categories'); return }
    onBack()
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-4">

      {/* Header */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={handleNavBack}
          className="px-3 py-1 text-sm border border-zinc-600 hover:border-zinc-400 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
        >
          ← Back
        </button>
        <h1 className="text-xl font-semibold text-zinc-100">Provision — dtc-box</h1>
      </div>

      {/* Category grid */}
      {view === 'categories' && (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">Select category</h2>
          <div className="grid grid-cols-3 gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.name}
                onClick={() => { setSelectedCategory(cat); setView('playbooks') }}
                className="px-3 py-3 text-left bg-zinc-700 hover:bg-zinc-600 border border-zinc-600 hover:border-zinc-500 rounded transition-colors"
              >
                <p className="text-zinc-200 text-sm font-medium">{cat.name}</p>
                <p className="text-zinc-500 text-xs mt-0.5">
                  {cat.playbooks.length} {cat.playbooks.length === 1 ? 'playbook' : 'playbooks'}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Playbook list */}
      {view === 'playbooks' && selectedCategory && (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-700">
            <p className="text-zinc-100 text-sm font-semibold">{selectedCategory.name}</p>
          </div>
          <div className="divide-y divide-zinc-700">
            {selectedCategory.playbooks.map((pb) => (
              <button
                key={pb.file}
                onClick={() => { setSelectedPlaybook(pb); setView('run') }}
                className="w-full text-left px-4 py-3 hover:bg-zinc-700 transition-colors"
              >
                <p className="text-zinc-200 text-sm font-medium">{pb.label}</p>
                <p className="text-zinc-500 text-xs mt-0.5">{pb.desc}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Run view */}
      {view === 'run' && selectedPlaybook && (
        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-5 space-y-4">
          <div>
            <p className="text-zinc-100 font-semibold text-sm">{selectedPlaybook.label}</p>
            <p className="text-zinc-400 text-xs mt-0.5">{selectedPlaybook.desc}</p>
          </div>
          <p className="text-zinc-500 text-xs font-mono">{selectedPlaybook.file}</p>
          <button
            className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors"
          >
            Run {selectedPlaybook.label}
          </button>
        </div>
      )}

    </div>
  )
}
