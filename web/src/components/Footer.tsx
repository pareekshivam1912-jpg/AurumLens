import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 py-3 px-6 text-xs text-slate flex flex-col sm:flex-row items-center justify-between gap-2 select-none">
      <div className="flex items-center space-x-2">
        <span className="font-semibold text-ink">AurumLens</span>
        <span>•</span>
        <strong className="text-slate font-medium">Analytics only — not investment advice.</strong>
        <span className="hidden md:inline">•</span>
        <span className="hidden md:inline text-slate-light">MCX Gold Cross-Contract RV Engine v2.1</span>
      </div>

      <div className="flex items-center space-x-4 text-[11px]">
        <Link href="/methodology" className="hover:text-gold transition-colors">
          Methodology Specs
        </Link>
        <Link href="/data-health" className="hover:text-gold transition-colors">
          Facts Register
        </Link>
        <Link href="/alerts" className="hover:text-gold transition-colors">
          Audit Trail
        </Link>
        <span className="font-mono text-slate-light">sha256:4a9977a</span>
      </div>
    </footer>
  );
}
