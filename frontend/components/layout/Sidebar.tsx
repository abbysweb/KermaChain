"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", desc: "Overview", emoji: "📊" },
  { href: "/chain", label: "Blockchain", desc: "Block explorer", emoji: "⛓" },
  { href: "/mempool", label: "Mempool", desc: "Pending transactions", emoji: "📋" },
  { href: "/peers", label: "Network", desc: "Peer connections", emoji: "🌐" },
  { href: "/learn", label: "Learn", desc: "How it works", emoji: "📖" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 glass-strong border-r border-white/30">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-black/5 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#4f6ef7] to-[#8b5cf6] text-sm font-bold text-white shadow-lg shadow-blue-500/20">
          K
        </div>
        <div>
          <h1 className="text-sm font-bold text-gray-900">KermaChain</h1>
          <p className="text-[10px] text-gray-400">Marabu Protocol Node</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-4 space-y-1 px-3">
        {navItems.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200",
                active
                  ? "bg-white/80 text-gray-900 shadow-sm border border-white/50"
                  : "text-gray-500 hover:bg-white/40 hover:text-gray-800"
              )}
            >
              <span className="text-base">{item.emoji}</span>
              <div>
                <span className="font-medium">{item.label}</span>
                <p className="text-[10px] text-gray-400">{item.desc}</p>
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Protocol badge */}
      <div className="mx-4 mt-6 rounded-xl bg-gradient-to-br from-[#4f6ef7]/10 to-[#8b5cf6]/10 border border-[#4f6ef7]/15 p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[#4f6ef7]">Protocol</p>
        <p className="mt-1 text-xs font-medium text-gray-700">Marabu P2P</p>
        <div className="mt-2 flex gap-2">
          <span className="rounded-full bg-[#10b981]/10 px-2 py-0.5 text-[9px] font-medium text-[#10b981]">Ed25519</span>
          <span className="rounded-full bg-[#f59e0b]/10 px-2 py-0.5 text-[9px] font-medium text-[#f59e0b]">UTXO</span>
        </div>
      </div>

      {/* Author */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-black/5 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#4f6ef7] to-[#8b5cf6] text-xs font-bold text-white shadow-md">
            AM
          </div>
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-gray-800">Abdullah Al Mamun</p>
            <p className="truncate text-[10px] text-gray-400">TU Wien & DIU</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
