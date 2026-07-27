"use client";

import type { MempoolEntry } from "@/lib/types";

function truncate(id: string, n = 10): string {
  return id.length > n * 2 ? `${id.slice(0, n)}...${id.slice(-n)}` : id;
}

interface MempoolTableProps {
  entries: MempoolEntry[];
}

export function MempoolTable({ entries }: MempoolTableProps) {
  if (entries.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 text-center">
        <p className="text-3xl mb-2">📭</p>
        <p className="text-sm font-medium text-gray-500">Mempool is empty</p>
        <p className="text-xs text-gray-400 mt-1">No pending transactions in the queue</p>
      </div>
    );
  }

  return (
    <div className="glass overflow-hidden rounded-2xl">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 text-left">
              <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Transaction ID
              </th>
              <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Inputs
              </th>
              <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Outputs
              </th>
              <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Total Value
              </th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr
                key={entry.txid}
                className="border-b border-gray-50 transition-colors hover:bg-white/40"
              >
                <td className="px-5 py-3">
                  <span className="font-mono text-xs text-[#10b981]">
                    {truncate(entry.txid)}
                  </span>
                </td>
                <td className="px-5 py-3 text-xs font-medium text-gray-600">
                  {entry.inputsCount}
                </td>
                <td className="px-5 py-3 text-xs font-medium text-gray-600">
                  {entry.outputsCount}
                </td>
                <td className="px-5 py-3 text-xs font-semibold text-[#f59e0b]">
                  {entry.totalValue.toLocaleString()} TMC
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
