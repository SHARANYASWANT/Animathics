import { useState, useEffect } from 'react'; 
import axios from 'axios';
import { Loader2, PlayCircle } from 'lucide-react';

const VideoGenerator = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('/api/history');
      const formatted = res.data.map(v => ({
        ...v,
        timestamp: new Date(v.timestamp)
      }));
      setHistory(formatted);
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!prompt) return;

    setLoading(true);
    setCurrentVideo(null);

    try {
      const res = await axios.post('/generate-video', { prompt });
      
      const newVideo = {
        url: res.data.videoUrl,
        prompt: prompt,
        timestamp: new Date()
      };

      setCurrentVideo(newVideo);
      
      fetchHistory(); 
      setPrompt('');
    } catch (err) {
      alert("Failed to generate video: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 w-full h-[calc(100vh-4rem)] overflow-y-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div className="lg:col-span-2 space-y-8">
           <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold mb-4">Create New Lesson</h2>
            <form onSubmit={handleGenerate} className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="E.g., Explain the Pythagorean theorem visually..."
                className="w-full h-32 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="animate-spin" /> : <PlayCircle />}
                {loading ? 'Generating Animation...' : 'Generate Video'}
              </button>
            </form>
          </div>

          {currentVideo && !loading && (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 animate-fade-in">
              <h3 className="font-semibold mb-3 text-lg">Result: {currentVideo.prompt}</h3>
              <video 
                src={currentVideo.url} 
                controls 
                autoPlay 
                className="w-full rounded-xl bg-black aspect-video"
              />
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit">
          <h2 className="font-bold text-gray-800 mb-4">Recent Videos</h2>
          {history.length === 0 ? (
            <p className="text-gray-400 text-sm">No videos generated yet.</p>
          ) : (
            <div className="space-y-4">
              {history.map((vid, idx) => (
                <div 
                  key={idx} 
                  className="group cursor-pointer p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition"
                  onClick={() => setCurrentVideo({ url: vid.videoUrl, prompt: vid.prompt })}
                >
                  <div className="aspect-video bg-gray-200 rounded-md mb-2 overflow-hidden relative">
                    <video src={vid.videoUrl} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                      <PlayCircle className="text-white" />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-700 line-clamp-2">{vid.prompt}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {vid.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default VideoGenerator;