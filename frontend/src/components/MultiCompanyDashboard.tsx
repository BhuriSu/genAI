import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Plus, Loader2 } from 'lucide-react';

interface FileInput {
  file: File | null;
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
  const [files, setFiles] = useState<FileInput[]>([{ file: null }]);
  const [loading, setLoading] = useState<boolean>(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAddFile = () => {
    setFiles([...files, { file: null }]);
  };

  const handleFileChange = (index: number, file: File | null) => {
    const newFiles = [...files];
    newFiles[index].file = file;
    setFiles(newFiles);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    const formData = new FormData();
  
    const validFiles = files.filter(entry => entry.file);
  
    if (validFiles.length === 0) {
      setError('Please select at least one file to analyze');
      setLoading(false);
      return;
    }
  
    validFiles.forEach((entry) => {
      if (entry.file) {
        formData.append("files", entry.file);
      }
    });
  
    try {
      const response = await fetch('http://localhost:8000/api/analyze-reports', {
        method: 'POST',
        // Remove credentials if not needed
        // credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
      });
  
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
  
      const data = await response.json();
      setAnalysisData(data.comparative_analysis);
    } catch (error) {
      console.error('Error analyzing reports:', error);
      setError(error instanceof Error ? error.message : 'An error occurred while analyzing reports');
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
            {files.map((file, index) => (
              <div key={index} className="flex gap-4 items-center">
                <input
                  type="file"
                  accept="application/pdf"
                  className="w-full p-2 border rounded"
                  onChange={(e) => handleFileChange(index, e.target.files?.[0] || null)}
                />
              </div>
            ))}
            <button
              onClick={handleAddFile}
              className="flex items-center gap-2 p-2 text-blue-600 hover:text-blue-800"
            >
              <Plus size={20} /> Add Another File
            </button>
            <button
              onClick={handleAnalyze}
              disabled={loading || !files.some(f => f.file)}
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
            {error && (
              <div className="text-red-500 mt-2">
                {error}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {analysisData && (
        <div className="space-y-6">
          {/* Revenue Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(analysisData.metrics.revenue).map(([file, value]) => ({
                      file: `File ${file}`,
                      revenue: value,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="file" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="revenue" fill="#3b82f6" name="Revenue ($M)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Gross Margin Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Gross Margin Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(analysisData.metrics.gross_margin).map(([file, value]) => ({
                      file: `File ${file}`,
                      margin: value,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="file" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="margin" fill="#22c55e" name="Gross Margin (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Net Income Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Net Income Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(analysisData.metrics.net_income).map(([file, value]) => ({
                      file: `File ${file}`,
                      income: value,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="file" />
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