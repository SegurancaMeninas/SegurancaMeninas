'use client';

import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, LineChart, Line, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, AreaChart, Area, Legend } from 'recharts';

const colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#14b8a6'];

export function SimpleBarChart({ data, xKey, yKey }: { data: Array<Record<string, unknown>>; xKey: string; yKey: string }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" />
        <XAxis dataKey={xKey} stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip />
        <Bar dataKey={yKey} fill="#0ea5e9" radius={[10, 10, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TrendChart({ data, xKey, yKey }: { data: Array<Record<string, unknown>>; xKey: string; yKey: string }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" />
        <XAxis dataKey={xKey} stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip />
        <Line type="monotone" dataKey={yKey} stroke="#22c55e" strokeWidth={3} dot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AreaTrendChart({ data, xKey, yKey }: { data: Array<Record<string, unknown>>; xKey: string; yKey: string }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.25)" />
        <XAxis dataKey={xKey} stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip />
        <Area type="monotone" dataKey={yKey} stroke="#0ea5e9" fill="url(#areaFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function PiePanel({ data, nameKey, valueKey }: { data: Array<Record<string, unknown>>; nameKey: string; valueKey: string }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Pie data={data} dataKey={valueKey} nameKey={nameKey} cx="50%" cy="50%" outerRadius={110} label>
          {data.map((_, index) => <Cell key={index} fill={colors[index % colors.length]} />)}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function RadarPanel({ data, keys }: { data: Array<Record<string, unknown>>; keys: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" />
        <Radar dataKey={keys[0]} stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.18} />
        {keys[1] ? <Radar dataKey={keys[1]} stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.12} /> : null}
        <Tooltip />
      </RadarChart>
    </ResponsiveContainer>
  );
}
