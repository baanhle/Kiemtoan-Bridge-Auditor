import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';
import {
  Calculator,
  History,
  BookOpen,
  MessageSquare,
  LogOut,
  Settings,
  Moon,
  Sun,
  Ruler,
  Layers,
  Zap,
  CheckCircle2,
  FileText,
  FileDown,
  Trash2,
  Send,
  Loader2,
  BarChart3
} from 'lucide-react';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

function App() {
  const [activeStandard, setActiveStandard] = useState('TCVN 11823:2017');

  const calculateEc = (fc, standard) => {
    if (!fc) return 0;
    if (standard === 'Eurocode') {
      // Eurocode 2: Ecm = 22 * ((fck + 8)/10)^0.3 (GPa) -> * 1000 for MPa
      return parseInt(22000 * Math.pow((fc + 8) / 10, 0.3));
    }
    // TCVN 11823 / AASHTO: Ec = 4800 * sqrt(fc)
    return parseInt(4800 * Math.sqrt(fc));
  };

  const handleStandardChange = (std) => {
    setActiveStandard(std);
    setInputs(prev => ({
      ...prev,
      materials: {
        ...prev.materials,
        E_c: calculateEc(prev.materials.f_c, std)
      }
    }));
  };
  const [activeTab, setActiveTab] = useState('results'); // 'results' or 'ai'
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  const INITIAL_STATE = {
    materials: { f_c: 35, E_c: 28397, f_y: 400, E_s: 200000, f_pu: 1860, f_py: 1674, E_p: 197000, f_pe: 1100, area_per_strand: 140 },
    geometry: { A: 1250000, I: 450000000, h: 2000, b_f: 1500, t_f: 250 },
    reinforcement: { n_bars: 0, d_bar: 32, y_s: 50, n_tendons: 1, n_strands: 40, y_p: 150 },
    loads: { Mu: 4500, Vu: 1200, Nu: 300 }
  };

  // Input State
  const [inputs, setInputs] = useState(INITIAL_STATE);

  const handleInputChange = (group, field, value) => {
    setInputs(prev => {
      const newInputs = {
        ...prev,
        [group]: {
          ...prev[group],
          [field]: parseFloat(value) || 0
        }
      };

      // Tự động tính các giá trị tương quan theo tiêu chuẩn
      if (group === 'materials') {
        if (field === 'f_c') {
          const fc = parseFloat(value) || 0;
          newInputs.materials.E_c = calculateEc(fc, activeStandard);
        }
        if (field === 'f_pu') {
          const fpu = parseFloat(value) || 0;
          newInputs.materials.f_py = parseInt(0.9 * fpu);
        }
      }
      return newInputs;
    });
  };

  const runAudit = async () => {
    setLoading(true);
    try {
      // Map inputs to the nested backend schema (TCVNAuditInput)
      const payload = {
        standard: activeStandard,
        materials: {
          f_c: inputs.materials.f_c,
          E_c: inputs.materials.E_c,
          f_y: inputs.materials.f_y,
          E_s: inputs.materials.E_s,
          f_pu: inputs.materials.f_pu,
          f_py: inputs.materials.f_py,
          E_p: inputs.materials.E_p,
          f_pe: inputs.materials.f_pe
        },
        geometry: {
          h: inputs.geometry.h,
          b: inputs.geometry.b_f,
          b_w: 400, // Default web width
          h_f: inputs.geometry.t_f,
          A_g: inputs.geometry.A,
          I_g: inputs.geometry.I
        },
        flexural_rebar: {
          A_s: inputs.reinforcement.n_bars * Math.PI * (inputs.reinforcement.d_bar / 2) ** 2,
          d_s: inputs.geometry.h - inputs.reinforcement.y_s,
          A_ps: inputs.reinforcement.n_tendons * inputs.reinforcement.n_strands * inputs.materials.area_per_strand,
          y_p: inputs.reinforcement.y_p,
          d_p: 0 // Sẽ tính ở Backend từ y_p
        },
        shear_rebar: {
          A_v: 628, // Default stirrup
          s: 200    // Default spacing
        },
        forces: {
          M_u: inputs.loads.Mu,
          V_u: inputs.loads.Vu,
          N_u: inputs.loads.Nu
        }
      };

      const response = await axios.post(`${API_BASE_URL}/api/audit`, payload);
      if (response.data.status === 'success') {
        setResults(response.data.data);
        setActiveTab('results');
      } else {
        alert("Lỗi từ Backend: " + response.data.detail);
      }
    } catch (error) {
      console.error("Audit failed:", error);
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          alert("LỖI NHẬP LIỆU (Validation):\n" + error.response.data.detail.map(d => `- ${d.msg}`).join('\n'));
        } else {
          alert("LỖI TỪ ENGINE (Toán học):\n" + error.response.data.detail);
        }
      } else {
        alert("Lỗi kết nối Backend. Vui lòng kiểm tra lại trạng thái Máy chủ Python!");
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async (format) => {
    if (!results) {
      alert("⚠️ Sếp ơi, Sếp nhập thông số và ấn 'CHẠY KIỂM TOÁN' trước thì em mới có dữ liệu để lập Báo cáo nhé!");
      return;
    }
    try {
      const response = await axios.post(`${API_BASE_URL}/api/report?format=${format}`, results, {
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      // Trích xuất tên file từ Server hoặc tự động gán
      const contentDisposition = response.headers['content-disposition'];
      let filename = `Bao_Cao_Kiem_Toan.${format === 'pdf' ? 'pdf' : 'docx'}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);

    } catch (error) {
      console.error(error);
      if (error.response && error.response.data instanceof Blob) {
        const text = await error.response.data.text();
        try {
          const json = JSON.parse(text);
          alert("LỖI XUẤT TỆP: " + (json.detail || "Chi tiết không xác định."));
        } catch {
          alert("Lỗi quá trình tải dữ liệu báo cáo.");
        }
      } else {
        alert("Lỗi kết nối máy chủ. Báo cáo chưa được sinh ra.");
      }
    }
  };

  return (
    <div className="flex h-screen bg-surface text-on-surface font-body overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="h-full w-20 bg-surface-container-low flex flex-col items-center py-6 gap-6 border-r border-outline-variant/20">
        <div className="bg-white text-primary p-3 rounded-xl shadow-sm border border-primary/10">
          <Calculator className="w-6 h-6" />
        </div>
        <button className="p-3 text-slate-400 hover:bg-surface-container-high rounded-xl transition-all">
          <History className="w-6 h-6" />
        </button>
        <button className="p-3 text-slate-400 hover:bg-surface-container-high rounded-xl transition-all">
          <BookOpen className="w-6 h-6" />
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={`p-3 rounded-xl transition-all ${activeTab === 'ai' ? 'text-primary bg-primary-fixed' : 'text-slate-400 hover:bg-surface-container-high'}`}
        >
          <MessageSquare className="w-6 h-6" />
        </button>
        <div className="mt-auto flex flex-col gap-4">
          <button className="p-3 text-slate-400 hover:bg-surface-container-high rounded-xl transition-all">
            <LogOut className="w-6 h-6" />
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="bg-surface flex justify-between items-center px-8 h-16 w-full border-b border-outline-variant/10 shadow-sm z-50">
          <div className="flex items-center gap-8">
            <span className="text-xl font-bold text-primary-container tracking-tighter font-headline">Kiểm Toán Mặt Cắt Cầu v1.0</span>
            <nav className="hidden md:flex gap-6 font-headline font-bold text-sm tracking-tight uppercase">
              {['TCVN 11823:2017', 'AASHTO LRFD', 'Eurocode'].map(std => (
                <button
                  key={std}
                  onClick={() => handleStandardChange(std)}
                  className={`${activeStandard === std ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-primary'} pb-1 transition-colors`}
                >
                  {std}
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right hidden lg:block">
              <p className="text-[10px] uppercase tracking-widest text-outline font-medium">Lê Bá Anh - Trường Đại học GTVT</p>
              <p className="text-primary-container text-sm font-semibold">Liên hệ: baanh.le@utc.edu.vn</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                <Moon className="w-5 h-5 text-outline" />
              </button>
              <button className="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                <Settings className="w-5 h-5 text-outline" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 flex overflow-hidden">
          {/* Main Content Layout (55% / 45%) */}
          <div className="flex-1 flex">
            {/* LEFT COLUMN: INPUTS */}
            <section className="w-[55%] flex flex-col h-full bg-surface-container-low border-r border-outline-variant/10">
              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                {/* Group 0: Vật liệu */}
                <div className="glass-card rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Layers className="text-primary w-5 h-5" />
                    <h2 className="text-lg font-bold font-headline uppercase tracking-tight">Đặc trưng Vật Liệu</h2>
                  </div>
                  <div className="space-y-6">
                    {/* Bê Tông */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-primary flex items-center gap-2 border-b border-outline-variant/20 pb-2">Bê tông</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          { key: 'f_c', label: "Cường độ nén f'c (MPa)" },
                          { key: 'E_c', label: "Mô đun đàn hồi Ec (MPa)" }
                        ].map((item) => (
                          <div key={item.key} className="space-y-1">
                            <label className="text-[10px] font-bold text-outline uppercase tracking-wider">{item.label}</label>
                            <input type="number" value={inputs.materials[item.key]} onChange={(e) => handleInputChange('materials', item.key, e.target.value)} className="w-full bg-surface-container-lowest border-0 border-b-2 border-transparent focus:border-primary focus:bg-white focus:ring-0 rounded-t-lg p-3 text-sm font-medium transition-all" />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Thép thường */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-primary flex items-center gap-2 border-b border-outline-variant/20 pb-2">Thép thường</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          { key: 'f_y', label: "Cường độ chảy fy (MPa)" },
                          { key: 'E_s', label: "Mô đun đàn hồi Es (MPa)" }
                        ].map((item) => (
                          <div key={item.key} className="space-y-1">
                            <label className="text-[10px] font-bold text-outline uppercase tracking-wider">{item.label}</label>
                            <input type="number" value={inputs.materials[item.key]} onChange={(e) => handleInputChange('materials', item.key, e.target.value)} className="w-full bg-surface-container-lowest border-0 border-b-2 border-transparent focus:border-primary focus:bg-white focus:ring-0 rounded-t-lg p-3 text-sm font-medium transition-all" />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Phép Dự Ứng Lực */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-primary flex items-center gap-2 border-b border-outline-variant/20 pb-2">Cáp dự ứng lực</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {[
                          { key: 'f_pu', label: "Kéo đứt fpu (MPa)" },
                          { key: 'f_py', label: "Giới hạn chảy fpy (MPa)" },
                          { key: 'E_p', label: "Mô đun đàn hồi Eps (MPa)" },
                          { key: 'f_pe', label: "Ư.suất hiệu quả fpe (MPa)" }
                        ].map((item) => (
                          <div key={item.key} className="space-y-1">
                            <label className="text-[10px] font-bold text-outline uppercase tracking-wider">{item.label}</label>
                            <input type="number" value={inputs.materials[item.key]} onChange={(e) => handleInputChange('materials', item.key, e.target.value)} className="w-full bg-surface-container-lowest border-0 border-b-2 border-transparent focus:border-primary focus:bg-white focus:ring-0 rounded-t-lg p-3 text-sm font-medium transition-all" />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Group 1: Hình học */}
                <div className="glass-card rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Ruler className="text-primary w-5 h-5" />
                    <h2 className="text-lg font-bold font-headline uppercase tracking-tight">Thông số Hình học</h2>
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    {Object.entries({
                      A: "Diện tích A (mm²)",
                      I: "Mô men quán tính I (mm⁴)",
                      h: "Chiều cao h (mm)",
                      b_f: "Bề rộng cánh (mm)",
                      t_f: "Chiều dày bản nắp (mm)"
                    }).map(([key, label]) => (
                      <div key={key} className="space-y-1.5">
                        <label className="text-[10px] font-bold text-outline uppercase tracking-wider">{label}</label>
                        <input
                          type="number"
                          value={inputs.geometry[key]}
                          onChange={(e) => handleInputChange('geometry', key, e.target.value)}
                          className="w-full bg-surface-container-low border-0 border-b-2 border-transparent focus:border-primary focus:bg-white focus:ring-0 rounded-t-lg p-3 text-sm font-medium transition-all"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Group 2: Cốt thép */}
                <div className="glass-card rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Layers className="text-primary w-5 h-5" />
                    <h2 className="text-lg font-bold font-headline uppercase tracking-tight">Cốt thép & Dự ứng lực</h2>
                  </div>
                  <div className="grid grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <h3 className="text-xs font-bold text-on-surface-variant flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-primary rounded-full"></span> Thép thường
                      </h3>
                      <div className="space-y-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Số lượng thanh</label>
                          <input type="number" value={inputs.reinforcement.n_bars} onChange={(e) => handleInputChange('reinforcement', 'n_bars', e.target.value)} className="w-full bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Đường kính (mm)</label>
                          <input type="number" value={inputs.reinforcement.d_bar} onChange={(e) => handleInputChange('reinforcement', 'd_bar', e.target.value)} className="w-full bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Khoảng cách đến đáy dầm (mm)</label>
                          <input type="number" value={inputs.reinforcement.y_s} onChange={(e) => handleInputChange('reinforcement', 'y_s', e.target.value)} className="w-full bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <h3 className="text-xs font-bold text-on-surface-variant flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-primary rounded-full"></span> Cáp dự ứng lực
                      </h3>
                      <div className="grid grid-cols-1 gap-4">
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Số bó / Số tao</label>
                          <div className="flex gap-2">
                            <input type="number" value={inputs.reinforcement.n_tendons} onChange={(e) => handleInputChange('reinforcement', 'n_tendons', e.target.value)} className="flex-1 bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                            <input type="number" value={inputs.reinforcement.n_strands} onChange={(e) => handleInputChange('reinforcement', 'n_strands', e.target.value)} className="flex-1 bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Diện tích 1 tao (mm2)</label>
                          <input type="number" value={inputs.materials.area_per_strand} onChange={(e) => handleInputChange('materials', 'area_per_strand', e.target.value)} className="w-full bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                        </div>
                        <div className="space-y-1">
                          <label className="text-[10px] font-bold text-outline uppercase">Khoảng cách từ đáy dầm đến cáp (mm)</label>
                          <input type="number" value={inputs.reinforcement.y_p} onChange={(e) => handleInputChange('reinforcement', 'y_p', e.target.value)} className="w-full bg-surface-container-low border-0 p-3 text-sm rounded-lg" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Group 3: Nội lực */}
                <div className="glass-card rounded-2xl p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Zap className="text-primary w-5 h-5" />
                    <h2 className="text-lg font-bold font-headline uppercase tracking-tight">Nội lực thiết kế</h2>
                  </div>
                  <div className="grid grid-cols-3 gap-6">
                    {Object.entries({
                      Mu: "Moment Mu (kNm)",
                      Vu: "Lực cắt Vu (kN)",
                      Nu: "Lực dọc Nu (kN)"
                    }).map(([key, label]) => (
                      <div key={key} className="space-y-1.5">
                        <label className="text-[10px] font-bold text-outline uppercase tracking-wider">{label}</label>
                        <input
                          type="number"
                          value={inputs.loads[key]}
                          onChange={(e) => handleInputChange('loads', key, e.target.value)}
                          className="w-full bg-surface-container-low border-0 border-b-2 border-transparent focus:border-primary focus:bg-white focus:ring-0 rounded-t-lg p-3 text-sm font-medium transition-all"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Footer */}
              <div className="p-6 bg-surface border-t border-outline-variant/10 flex gap-4 items-center">
                <button
                  onClick={runAudit}
                  disabled={loading}
                  className="flex-1 bg-primary text-white font-bold py-4 rounded-2xl shadow-lg shadow-primary/20 hover:scale-[0.99] active:scale-[0.97] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <BarChart3 className="w-5 h-5" />}
                  CHẠY KIỂM TOÁN
                </button>
                <button
                  onClick={() => { if (window.confirm('Khôi phục dữ liệu gốc?')) setInputs(INITIAL_STATE) }}
                  className="px-6 py-4 bg-white text-error border border-error/20 font-bold rounded-2xl hover:bg-error-container/10 transition-all flex items-center justify-center gap-2"
                  title="Nhập lại từ đầu"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </section>

            {/* RIGHT COLUMN: RESULTS & AI */}
            <section className="w-[45%] h-full bg-surface flex flex-col">
              {/* Tabs */}
              <div className="flex p-1.5 bg-surface-container-low m-6 rounded-2xl border border-outline-variant/10">
                <button
                  onClick={() => setActiveTab('results')}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all ${activeTab === 'results' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:bg-surface-container-high'}`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Kết quả
                </button>
                <button
                  onClick={() => setActiveTab('ai')}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all ${activeTab === 'ai' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:bg-surface-container-high'}`}
                >
                  <MessageSquare className="w-4 h-4" />
                  Trợ lý AI
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-8 pb-8">
                {activeTab === 'results' ? (
                  <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
                    {results ? (
                      <>
                        {/* Summary Card */}
                        <div className={`relative overflow-hidden rounded-3xl p-8 text-white shadow-xl ${results.overall_status === 'ĐẠT' ? 'bg-gradient-to-br from-[#006875] to-[#004e58]' : 'bg-gradient-to-br from-error to-[#93000a]'}`}>
                          <div className="relative z-10">
                            <div className="flex items-center gap-2 mb-2 opacity-90">
                              <CheckCircle2 className="w-4 h-4" />
                              <span className="text-[10px] font-bold uppercase tracking-[0.2em]">Trạng thái</span>
                            </div>
                            <h2 className="text-4xl font-extrabold font-headline mb-4 tracking-tighter uppercase">
                              {results.overall_status === 'ĐẠT' ? 'ĐẠT YÊU CẦU' : 'KHÔNG ĐẠT'}
                            </h2>
                            {results.overall_status === 'KHÔNG ĐẠT' && (
                              <div className="bg-white/20 p-3 rounded-xl backdrop-blur-md border border-white/30 text-xs font-medium space-y-1">
                                <p className="opacity-100 font-bold underline">Phân tích lỗi (Sếp chú ý!):</p>
                                {(results.flexural.ratio > 1 || results.shear.ratio > 1) && (
                                  <p>⚠️ "Thiếu diện tích cốt thép": Nội lực MU/VU lớn hơn sức kháng của mặt cắt. Sếp hãy thử tăng số bó cáp, tao cáp hoặc thêm cốt thép thường nếu cần nhé.</p>
                                )}
                                {results.flexural.details.includes('phá hoại dẻo') && (
                                  <p>⚠️ "Vi phạm điều kiện phá hoại dẻo" (c/de ≤ 0.42): Cần giảm lượng thép hoặc tăng kích thước bê tông để tránh dầm bị phá hoại giòn đột ngột.</p>
                                )}
                              </div>
                            )}
                            <p className="text-sm opacity-80 max-w-xs leading-relaxed mt-4">
                              Mặt cắt đã được kiểm tra theo {activeStandard}.
                            </p>
                          </div>
                          <CheckCircle2 className="absolute -bottom-6 -right-6 w-48 h-48 opacity-10 rotate-12" />
                        </div>

                        {/* Ratios */}
                        <div className="space-y-6">
                          <h3 className="text-xs font-bold text-outline uppercase tracking-widest flex items-center gap-2">
                            <span className="w-8 h-[1px] bg-outline-variant"></span> Tỉ lệ sức kháng (%)
                          </h3>
                          {[
                            {
                              label: 'Sức kháng uốn (Moment)',
                              ratio: (results.flexural.ratio * 100).toFixed(1),
                              desc: `Mn = ${results.flexural.capacity.toFixed(1)} kNm (Y/c: ${results.flexural.demand.toFixed(1)})`
                            },
                            {
                              label: 'Sức kháng cắt (Shear)',
                              ratio: (results.shear.ratio * 100).toFixed(1),
                              desc: `Vn = ${results.shear.capacity.toFixed(1)} kN (Y/c: ${results.shear.demand.toFixed(1)})`
                            }
                          ].map((item, idx) => (
                            <div key={idx} className="space-y-2">
                              <div className="flex justify-between items-end">
                                <div className="flex flex-col gap-0.5">
                                  <span className="text-sm font-bold text-slate-800 tracking-tight">{item.label}</span>
                                  <div className="flex items-center gap-1.5 font-mono text-[12px]">
                                    <span className="bg-slate-100 px-1.5 py-0.5 rounded text-primary font-bold">{item.desc.split(' (')[0]}</span>
                                    <span className="text-slate-400 scale-90">{item.desc.split(' (')[1].replace(')', '')}</span>
                                  </div>
                                </div>
                                <span className="text-lg font-bold font-headline text-primary">{item.ratio}%</span>
                              </div>
                              <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-1000 ${parseFloat(item.ratio) > 100 ? 'bg-error' : 'bg-primary'}`}
                                  style={{ width: `${Math.min(parseFloat(item.ratio), 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Actions */}
                        <div className="flex gap-4 pt-4">
                          <button onClick={() => downloadReport('word')} className="flex-1 flex items-center justify-center gap-2 border-2 border-primary/10 py-4 rounded-2xl font-bold text-primary hover:bg-primary/5 transition-all">
                            <FileText className="w-5 h-5" />
                            WORD
                          </button>
                          <button onClick={() => downloadReport('pdf')} className="flex-1 flex items-center justify-center gap-2 border-2 border-primary/10 py-4 rounded-2xl font-bold text-primary hover:bg-primary/5 transition-all">
                            <FileDown className="w-5 h-5" />
                            PDF
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="h-64 border-2 border-dashed border-outline-variant/30 rounded-3xl flex flex-col items-center justify-center text-outline-variant gap-4">
                        <BarChart3 className="w-12 h-12 opacity-20" />
                        <p className="text-sm font-medium">Chưa có kết quả kiểm toán</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col h-[500px] border border-outline-variant/10 rounded-3xl bg-surface-container-lowest overflow-hidden">
                    <div className="flex-1 p-6 space-y-4 overflow-y-auto pb-4">
                      <div className="bg-surface-container-low p-4 rounded-2xl rounded-tl-none max-w-[80%]">
                        <p className="text-sm text-on-surface-variant leading-relaxed">
                          Xin chào Sếp! Em là Trợ lý kỹ thuật của Sếp đây. <br /><br />Hiện tại em đang chờ Sếp cấu hình API Key ở phần Cài đặt hệ thống để có thể soi bản vẽ cùng Sếp nhé. Tạm thời Sếp cứ xem thông số máy tính trước nha! ✨
                        </p>
                      </div>
                      {aiLoading && (
                        <div className="bg-surface-container-low p-4 rounded-2xl rounded-tl-none max-w-[80%] self-start flex items-center gap-2 mt-4">
                          <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          <span className="text-sm">Trợ lý kỹ thuật đang phân tích...</span>
                        </div>
                      )}
                      {aiResponse && (
                        <div className="bg-primary/10 border border-primary/20 p-4 rounded-2xl rounded-tr-none max-w-[80%] self-end mt-4 shadow-sm">
                          <p className="text-sm text-primary-container font-medium whitespace-pre-wrap">{aiResponse}</p>
                        </div>
                      )}
                    </div>
                    <div className="p-4 border-t border-outline-variant/10 bg-white shadow-[0_-10px_20px_rgba(0,0,0,0.02)]">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={aiQuery}
                          onChange={(e) => setAiQuery(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && aiQuery.trim() && !aiLoading) {
                              setAiLoading(true);
                              setTimeout(() => {
                                setAiResponse("Sếp ơi, chức năng Gọi AI Explaination v2 đang đợi em tích hợp bảng Setting API Key lên Frontend. Sếp vui vẻ xài đỡ bản tính toán thuần tuý nha! 🥰");
                                setAiQuery('');
                                setAiLoading(false);
                              }, 1200);
                            }
                          }}
                          placeholder="Hỏi Trợ lý kỹ thuật về kết quả này..."
                          className="flex-1 border-0 bg-surface-container-lowest border-outline-variant/20 border shadow-inner rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary focus:outline-none transition-all"
                        />
                        <button
                          onClick={() => {
                            if (aiQuery.trim() && !aiLoading) {
                              setAiLoading(true);
                              setTimeout(() => {
                                setAiResponse("Sếp ơi, chức năng Gọi AI Explaination v2 đang đợi em tích hợp bảng Setting API Key lên Frontend. Sếp vui vẻ xài đỡ bản tính toán thuần tuý nha! 🥰");
                                setAiQuery('');
                                setAiLoading(false);
                              }, 1200);
                            }
                          }}
                          className="bg-primary hover:bg-[#004e58] text-white p-3 rounded-xl shadow-md transition-all active:scale-95 disabled:opacity-50"
                          disabled={aiLoading}
                        >
                          <Send className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          </div>
        </main>

        <footer className="bg-surface w-full py-4 border-t border-outline-variant/10 flex flex-col items-center justify-center gap-1">
          <p className="text-[10px] uppercase tracking-widest font-medium text-slate-400">
            © 2024 Trường Đại học GTVT - UTC. All Rights Reserved.
          </p>
        </footer>
      </div>
    </div>
  );
}

// Vercel Auto-deploy trigger: Updated UI and Calculation Logic - 2026-03-23
export default App;
