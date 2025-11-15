import { useEffect, useState } from 'react';
import { getLatestReading, ReadingData } from '@/lib/db';
import MetricCard from '@/components/MetricCard';
import GaugeChart from '@/components/GaugeChart';
import { Activity, Gauge, Zap } from 'lucide-react';

export default function Index() {
  const [data, setData] = useState<ReadingData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const reading = await getLatestReading();
        if (reading) {
          setData(reading);
          setLastUpdate(new Date().toLocaleTimeString());
        }
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Set up polling every 1 second
    const interval = setInterval(fetchData, 1000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent mb-2">
            Automotive Dashboard
          </h1>
          <p className="text-slate-400">
            Real-time engine monitoring • Last update: {lastUpdate}
          </p>
        </div>

        {/* Gauges Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <GaugeChart
            value={data?.RPM || 0}
            max={8000}
            label="Engine RPM"
            unit="RPM"
            colorClass="stroke-blue-500"
          />
          <GaugeChart
            value={data?.SPEED || 0}
            max={200}
            label="Vehicle Speed"
            unit="km/h"
            colorClass="stroke-cyan-500"
          />
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricCard
            title="Engine RPM"
            value={data?.RPM || 0}
            unit="RPM"
            icon={<Activity className="w-4 h-4" />}
            colorClass="text-blue-500"
          />
          <MetricCard
            title="Vehicle Speed"
            value={data?.SPEED || 0}
            unit="km/h"
            icon={<Gauge className="w-4 h-4" />}
            colorClass="text-cyan-500"
          />
          <MetricCard
            title="Engine Load"
            value={data?.ENGINE_LOAD || 0}
            unit="%"
            icon={<Zap className="w-4 h-4" />}
            colorClass="text-green-500"
          />
        </div>

        {/* Status Indicator */}
        <div className="mt-8 flex items-center justify-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-slate-400">Live Data Stream Active</span>
        </div>
      </div>
    </div>
  );
}