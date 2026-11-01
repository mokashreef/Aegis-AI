import { CompanionOverlay } from "./components/CompanionOverlay";

export function App() {
  return (
    <div className="w-full h-full flex flex-col bg-[#0b0f19] text-slate-100 overflow-hidden select-none">
      <CompanionOverlay />
    </div>
  );
}

export default App;
