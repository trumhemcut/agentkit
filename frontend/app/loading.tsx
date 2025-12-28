export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-800">Loading AgentKit</h2>
        <p className="text-gray-600 mt-2">Initializing AI agents...</p>
      </div>
    </div>
  );
}
