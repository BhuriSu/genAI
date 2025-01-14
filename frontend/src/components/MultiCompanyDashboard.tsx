import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Plus, Loader2 } from 'lucide-react';

interface UrlInput {
  company: string;
  url: string;
}

interface Metrics {
  revenue: Record<string, number>;
  gross_margin: Record<string, number>;
  net_income: Record<string, number>;
}

interface AnalysisData {
  metrics: Metrics;
}

const MultiCompanyDashboard: React.FC = () => {
  const [urls, setUrls] = useState<UrlInput[]>([{ company: '', url: '' }]);
  const [loading, setLoading] = useState<boolean>(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

  const handleAddUrl = () => {
    setUrls([...urls, { company: '', url: '' }]);
  };

  const handleInputChange = (index: number, field: keyof UrlInput, value: string) => {
    const newUrls = [...urls];
    newUrls[index][field] = value;
    setUrls(newUrls);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/analyze-reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(
          urls.filter(url => url.company && url.url)
        ),
      });
      const data = await response.json();
      setAnalysisData(data.comparative_analysis);
    } catch (error) {
      console.error('Error analyzing reports:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Financial Reports Analyzer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {urls.map((url, index) => (
              <div key={index} className="flex gap-4">
                <input
                  type="text"
                  placeholder="Company Name"
                  className="flex-1 p-2 border rounded"
                  value={url.company}
                  onChange={(e) => handleInputChange(index, 'company', e.target.value)}
                />
                <input
                  type="text"
                  placeholder="PDF URL"
                  className="flex-1 p-2 border rounded"
                  value={url.url}
                  onChange={(e) => handleInputChange(index, 'url', e.target.value)}
                />
              </div>
            ))}
            <button
              onClick={handleAddUrl}
              className="flex items-center gap-2 p-2 text-blue-600 hover:text-blue-800"
            >
              <Plus size={20} /> Add Another Company
            </button>
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full p-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="animate-spin" /> Analyzing Reports...
                </span>
              ) : (
                'Analyze Reports'
              )}
            </button>
          </div>
        </CardContent>
      </Card>

      {analysisData && (
        <div className="space-y-6">
          {/* Revenue Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(analysisData.metrics.revenue).map(([company, value]) => ({
                    company,
                    revenue: value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="company" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="revenue" fill="#3b82f6" name="Revenue ($M)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Gross Margin Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Gross Margin Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(analysisData.metrics.gross_margin).map(([company, value]) => ({
                    company,
                    margin: value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="company" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="margin" fill="#22c55e" name="Gross Margin (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Net Income Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Net Income Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(analysisData.metrics.net_income).map(([company, value]) => ({
                    company,
                    income: value
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="company" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="income" fill="#ef4444" name="Net Income ($M)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MultiCompanyDashboard;