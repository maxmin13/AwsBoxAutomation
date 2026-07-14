import { useAuth } from '../AuthContext'
import PricingLink from '../components/PricingLink'

export default function CreateVmPage() {
  const { requireCreds, withAuth } = useAuth()

  const config = [
    { label: 'Instance name',   value: 'dtc-box'                             },
    { label: 'AMI',             value: 'Amazon Linux 2 (amzn2 kernel 5.10)'  },
    { label: 'Instance type',   value: 't3.micro'                            },
    { label: 'Region / AZ',     value: 'eu-west-1 / eu-west-1a'             },
    { label: 'VPC',             value: 'dtc-datacenter  ·  10.0.0.0/16'     },
    { label: 'Subnet',          value: 'dtc-subnet  ·  10.0.20.0/24'        },
    { label: 'Private IP',      value: '10.0.20.35'                          },
    { label: 'Security group',  value: 'dtc-sgp  ·  ICMP, 22, 8080, 8443, 5432' },
    { label: 'DNS record',      value: 'dtc.maxmin.it  (Route 53)'           },
  ]

  return (
    <div className="max-w-2xl mx-auto">

      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-zinc-100">Create VM</h1>
        <p className="text-zinc-500 text-sm mt-1">
          Creates VPC, subnet, security group, EC2 instance, and DNS record on AWS.
        </p>
        <p className="text-zinc-600 text-xs mt-1">
          EC2 instance billed while running · {' '}
          <PricingLink url="https://aws.amazon.com/ec2/pricing/" label="EC2 pricing ↗" /> ·{' '}
          <PricingLink url="https://aws.amazon.com/route53/pricing/" label="Route 53 pricing ↗" />
        </p>
      </div>

      {/* Config summary */}
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden mb-6">
        <div className="px-4 py-3 border-b border-zinc-700">
          <p className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Configuration</p>
        </div>
        <dl className="divide-y divide-zinc-700">
          {config.map(({ label, value }) => (
            <div key={label} className="px-4 py-3 flex justify-between gap-4">
              <dt className="text-zinc-500 text-sm shrink-0">{label}</dt>
              <dd className="text-zinc-200 text-sm font-mono text-right">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <button
        onClick={() => requireCreds(() => withAuth(() => { /* TODO: trigger VM creation */ }))}
        className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 text-white font-medium rounded transition-colors"
      >
        Create VM
      </button>

    </div>
  )
}
