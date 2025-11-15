interface GaugeChartProps {
  value: number;
  max: number;
  label: string;
  unit: string;
  colorClass?: string;
}

export default function GaugeChart({ value, max, label, unit, colorClass = 'stroke-blue-500' }: GaugeChartProps) {
  const percentage = Math.min((value / max) * 100, 100);
  const circumference = 2 * Math.PI * 90;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-slate-900 rounded-lg border border-slate-700">
      <div className="relative w-48 h-48">
        <svg className="transform -rotate-90 w-48 h-48">
          <circle
            cx="96"
            cy="96"
            r="90"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            className="text-slate-800"
          />
          <circle
            cx="96"
            cy="96"
            r="90"
            stroke="currentColor"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className={`${colorClass} transition-all duration-500 ease-out`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold text-white">{value.toFixed(0)}</span>
          <span className="text-sm text-slate-400">{unit}</span>
        </div>
      </div>
      <div className="mt-4 text-center">
        <p className="text-lg font-semibold text-slate-300">{label}</p>
        <p className="text-xs text-slate-500">Max: {max} {unit}</p>
      </div>
    </div>
  );
}