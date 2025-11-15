import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MetricCardProps {
  title: string;
  value: number | string;
  unit: string;
  icon?: React.ReactNode;
  colorClass?: string;
}

export default function MetricCard({ title, value, unit, icon, colorClass = 'text-blue-500' }: MetricCardProps) {
  return (
    <Card className="bg-slate-900 border-slate-700 hover:border-slate-600 transition-all">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-4xl font-bold ${colorClass}`}>
            {typeof value === 'number' ? value.toFixed(1) : value}
          </span>
          <span className="text-xl text-slate-500">{unit}</span>
        </div>
      </CardContent>
    </Card>
  );
}