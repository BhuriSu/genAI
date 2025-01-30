import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Plus, Loader2, FileText, Image, Box } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Types
interface FileInput {
  file: File | null;
}

interface FinancialMetrics {
  revenue: Record<string, number>;
  gross_margin: Record<string, number>;
  net_income: Record<string, number>;
}

interface AnalysisData {
  metrics: FinancialMetrics;
  summary: string;
  trends: string[];
  recommendations: string[];
}

interface GeneratedContent {
  text?: string;
  imageUrl?: string;
  content2D?: string; 
  content3D?: string;
}

const MultiServiceDashboard = () => {
  // State management
  const [files, setFiles] = useState<FileInput[]>([{ file: null }]);
  const [loading, setLoading] = useState<boolean>(false);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'financial' | 'content'>('financial');
  const [prompt, setPrompt] = useState<string>('');
  const [generationType, setGenerationType] = useState<'text' | 'text2D' | 'text3D' | 'image' | 'image3D'>('text');
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);

  // Get the appropriate API endpoint based on generation type
  const getApiEndpoint = (type: string) => {
    const endpoints = {
      text: 'http://localhost:8000/api/generate/text',
      text2D: 'http://localhost:8000/api/generate/text/2D',
      text3D: 'http://localhost:8000/api/generate/text/3D',
      image: 'http://localhost:8000/api/generate/image/2D',
      image3D: 'http://localhost:8000/api/generate/image/3D'
    };
    return endpoints[type as keyof typeof endpoints];
  };

  // Handlers for financial analysis remain the same
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
        body: formData,
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Updated generate handler to use the correct endpoint
  const handleGenerate = async () => {
    if (!prompt) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const endpoint = getApiEndpoint(generationType);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      
      // Process the response based on generation type
      const newContent: GeneratedContent = {};
      if (generationType === 'text') {
        newContent.text = data.text;
      } else if (generationType.includes('image')) {
        newContent.imageUrl = data.imageUrl;
      } else if (generationType === 'text2D') {
        newContent.content2D = data.content;
      } else if (generationType === 'text3D') {
        newContent.content3D = data.content;
      }
      
      setGeneratedContent(newContent);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Service Selection Tabs */}
      <div className="flex space-x-4 border-b">
        <button
          className={`pb-2 px-4 ${activeTab === 'financial' ? 'border-b-2 border-blue-600 text-blue-600' : ''}`}
          onClick={() => setActiveTab('financial')}
        >
          Financial Analysis
        </button>
        <button
          className={`pb-2 px-4 ${activeTab === 'content' ? 'border-b-2 border-blue-600 text-blue-600' : ''}`}
          onClick={() => setActiveTab('content')}
        >
          Content Generation
        </button>
      </div>

      {/* Financial Analysis Section */}
      {activeTab === 'financial' && (
        <div className="space-y-6">
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
                      accept="application/pdf,.csv,.xlsx"
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
                      <Loader2 className="animate-spin" /> Analyzing...
                    </span>
                  ) : (
                    'Analyze Reports'
                  )}
                </button>
              </div>
            </CardContent>
          </Card>

          {analysisData && (
            <>
              {/* Financial Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>Key Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={Object.entries(analysisData.metrics.revenue).map(([date, value]) => ({
                        date,
                        revenue: value,
                        grossMargin: analysisData.metrics.gross_margin[date],
                        netIncome: analysisData.metrics.net_income[date]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
                        <Line type="monotone" dataKey="grossMargin" stroke="#82ca9d" />
                        <Line type="monotone" dataKey="netIncome" stroke="#ffc658" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Analysis Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p className="text-gray-700">{analysisData.summary}</p>
                    <div>
                      <h4 className="font-semibold mb-2">Key Trends</h4>
                      <ul className="list-disc pl-5 space-y-1">
                        {analysisData.trends.map((trend, index) => (
                          <li key={index}>{trend}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Recommendations</h4>
                      <ul className="list-disc pl-5 space-y-1">
                        {analysisData.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

        {/* Content Generation Section */}
        {activeTab === 'content' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Content Generator</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <button
                    onClick={() => setGenerationType('text')}
                    className={`flex items-center gap-2 p-2 rounded ${
                      generationType === 'text' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                    }`}
                  >
                    <FileText size={20} /> Text
                  </button>
                  <button
                    onClick={() => setGenerationType('text2D')}
                    className={`flex items-center gap-2 p-2 rounded ${
                      generationType === 'text2D' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                    }`}
                  >
                    <Image size={20} /> Text to 2D
                  </button>
                  <button
                    onClick={() => setGenerationType('text3D')}
                    className={`flex items-center gap-2 p-2 rounded ${
                      generationType === 'text3D' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                    }`}
                  >
                    <Box size={20} /> Text to 3D
                  </button>
                  <button
                    onClick={() => setGenerationType('image')}
                    className={`flex items-center gap-2 p-2 rounded ${
                      generationType === 'image' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                    }`}
                  >
                  <Image size={20} /> Image
                  </button>
                  <button
                    onClick={() => setGenerationType('image3D')}
                    className={`flex items-center gap-2 p-2 rounded ${
                      generationType === 'image3D' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                    }`}
                  >
                    <Box size={20} /> Image to 3D
                  </button>
                </div>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={`Enter your ${generationType} generation prompt...`}
                  className="w-full p-2 border rounded h-32"
                />
                <button
                  onClick={handleGenerate}
                  disabled={loading || !prompt}
                  className="w-full p-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="animate-spin" /> Generating...
                    </span>
                  ) : (
                    'Generate Content'
                  )}
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Generated Content Display */}
          {generatedContent && (
            <Card>
              <CardHeader>
                <CardTitle>Generated Content</CardTitle>
              </CardHeader>
              <CardContent>
                {generationType === 'text' && generatedContent.text && (
                  <div className="prose max-w-none">
                    {generatedContent.text}
                  </div>
                )}
                {generationType === 'image' && generatedContent.imageUrl && (
                  <div className="flex justify-center">
                    <img
                      src={generatedContent.imageUrl}
                      alt="Generated content"
                      className="max-w-full h-auto rounded-lg shadow-lg"
                    />
                  </div>
                )}
                {generationType === 'text2D' && generatedContent.content2D && (
                  <div className="prose max-w-none">
                    {generatedContent.content2D}
                  </div>
                )}
                {generationType === 'text3D' && generatedContent.content3D && (
                  <div className="prose max-w-none">
                    {generatedContent.content3D}
                  </div>
                )}
                {generationType === 'image3D' && generatedContent.imageUrl && (
                  <div className="flex justify-center">
                    <img
                      src={generatedContent.imageUrl}
                      alt="Generated 3D content"
                      className="max-w-full h-auto rounded-lg shadow-lg"
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {error && (
        <div className="text-red-500 mt-2">
          {error}
        </div>
      )}
    </div>
  );
};

export default MultiServiceDashboard;