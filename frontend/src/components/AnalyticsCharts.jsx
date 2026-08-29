import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const palette = ["#6947c8", "#9b66ef", "#3d9b68", "#d39b3f", "#c74b69", "#5383cf"];

function ChartEmpty({ message = "No data available for this chart." }) {
  return <div className="analytics-chart-empty">{message}</div>;
}

export function AnalyticsBarChart({ data, dataKey, name, color = "#6947c8", labelKey = "label", valueFormatter }) {
  if (!data?.length) return <ChartEmpty />;
  return <div className="analytics-chart"><ResponsiveContainer width="100%" height={260}><BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><XAxis dataKey={labelKey} tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip formatter={valueFormatter ? (value) => valueFormatter(value) : undefined} /><Legend /><Bar dataKey={dataKey} name={name} fill={color} radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div>;
}

export function AnalyticsLineChart({ data, dataKey, name, color = "#6947c8", labelKey = "label", valueFormatter }) {
  if (!data?.length) return <ChartEmpty />;
  return <div className="analytics-chart"><ResponsiveContainer width="100%" height={260}><LineChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><XAxis dataKey={labelKey} tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip formatter={valueFormatter ? (value) => valueFormatter(value) : undefined} /><Legend /><Line type="monotone" dataKey={dataKey} name={name} stroke={color} strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer></div>;
}

export function AnalyticsDonutChart({ data }) {
  if (!data?.length || !data.some((item) => Number(item.value) > 0)) return <ChartEmpty />;
  return <div className="analytics-chart"><ResponsiveContainer width="100%" height={260}><PieChart><Pie data={data} dataKey="value" nameKey="label" innerRadius={62} outerRadius={90} paddingAngle={3}>{data.map((item, index) => <Cell key={item.label} fill={palette[index % palette.length]} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div>;
}
