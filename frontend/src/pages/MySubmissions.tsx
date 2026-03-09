import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import { api } from '../services/api';
import type { Submission } from '../types';
import { getAuthUser } from '../lib/auth';
import { formatShanghaiDateTime } from '../lib/datetime';
import { getNewspaperTheme } from '../lib/newspapers';

export default function MySubmissions() {
  const { t } = useTranslation();
  const authUser = getAuthUser();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [guestPenName, setGuestPenName] = useState('匿名');

  const loadSubmissions = async (penName?: string) => {
    setLoading(true);
    setError('');
    try {
      const data = authUser
        ? await api.getMySubmissions()
        : await api.getUserSubmissions((penName || guestPenName || '匿名').trim());
      setSubmissions(data);
    } catch (err: any) {
      setSubmissions([]);
      setError(err.message || t('mySubmissions.loadError'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubmissions(authUser?.pen_name || '匿名');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'pending':
        return { text: t('mySubmissions.statusPending'), color: 'bg-yellow-100 text-yellow-800 border-yellow-300' };
      case 'reviewing':
        return { text: t('mySubmissions.statusReviewing'), color: 'bg-blue-100 text-blue-800 border-blue-300' };
      case 'approved':
        return { text: t('mySubmissions.statusApproved'), color: 'bg-green-100 text-green-800 border-green-300' };
      case 'rejected':
        return { text: t('mySubmissions.statusRejected'), color: 'bg-red-100 text-red-800 border-red-300' };
      case 'queued_overflow':
        return { text: t('mySubmissions.statusQueued'), color: 'bg-purple-100 text-purple-800 border-purple-300' };
      default:
        return { text: t('mySubmissions.statusUnknown'), color: 'bg-gray-100 text-gray-800 border-gray-300' };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'reviewing':
        return '🔍';
      case 'approved':
        return '✅';
      case 'rejected':
        return '❌';
      case 'queued_overflow':
        return '🧾';
      default:
        return '❓';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream">
        <Header />
        <div className="text-center py-20">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-[#d4c9b5] border-t-[#d4652f] rounded-full"></div>
          <p className="mt-4 text-[#9c8b75] font-mono">{t('mySubmissions.loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream">
      <Header />
      
      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold text-ink-dark mb-2">{t('nav.mySubmissions')}</h1>
          <div className="divider-ornament">
            <span>📋</span>
          </div>
          <p className="text-[#6b5c4d]">记录每一次表达的开始与结束</p>
          <p className="text-sm text-[#9c8b75] mt-2">
            {authUser ? `当前账号：@${authUser.username}` : t('mySubmissions.guestMode')}
          </p>
        </div>

        {!authUser && (
          <div className="mb-6 paper-texture border border-[#d4c9b5] p-4 flex flex-col md:flex-row gap-3">
            <input
              type="text"
              value={guestPenName}
              onChange={(e) => setGuestPenName(e.target.value)}
              className="input-vintage"
              placeholder={t('submitForm.penNamePlaceholder')}
            />
            <button
              type="button"
              className="btn-vintage whitespace-nowrap"
              onClick={() => loadSubmissions(guestPenName)}
            >
              {t('mySubmissions.queryByPenName')}
            </button>
            <Link to="/login" className="btn-vintage whitespace-nowrap text-center">
              {t('nav.login')}
            </Link>
          </div>
        )}

        {error && (
          <div className="mb-6 p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}
        
        {submissions.length === 0 ? (
          <div className="text-center py-20 paper-texture border-2 border-dashed border-[#d4c9b5]">
            <div className="text-4xl mb-4">📝</div>
            <p className="text-[#9c8b75] font-serif italic">
              {t('mySubmissions.noSubmissions')}
            </p>
            <Link to="/submit" className="btn-vintage inline-flex items-center space-x-2 mt-6">
              <span>{t('nav.submit')}</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {submissions.map((s) => {
              const statusConfig = getStatusConfig(s.status);
              const paper = getNewspaperTheme(s.newspaper_slug);
              
              return (
                <div 
                  key={s.id} 
                  className="paper-texture border-2 border-[#d4c9b5] p-6 hover:border-[#9c8b75] transition-colors group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-bold text-xl text-ink-dark mb-1 group-hover:text-[#d4652f] transition-colors">
                        {s.title}
                      </h3>
                      <div className="flex items-center space-x-3 text-xs font-mono text-[#9c8b75]">
                        <span>{s.newspaper_name || '未知报纸'}</span>
                        <span>·</span>
                        <span>{formatShanghaiDateTime(s.submitted_at)}</span>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded text-xs font-medium border ${statusConfig.color}`}>
                      {getStatusIcon(s.status)} {statusConfig.text}
                    </span>
                  </div>
                  
                  <p className="text-sm text-[#6b5c4d] line-clamp-2 mb-4 font-serif">
                    {s.content || '（投稿内容仅在详情页展示）'}
                  </p>

                  {(s.status === 'rejected' || s.status === 'queued_overflow') && s.rejection_reason && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded">
                      <p className="text-xs font-mono uppercase tracking-wider text-red-700 mb-1">
                        {s.status === 'rejected' ? '拒稿原因' : '系统提示'}
                      </p>
                      <p className="text-sm text-[#7f1d1d] whitespace-pre-line">
                        {s.rejection_reason}
                      </p>
                    </div>
                  )}

                  {(s.score !== undefined || s.status === 'approved' || s.status === 'rejected') && (
                    <div className="flex items-center justify-between pt-3 border-t border-[#d4c9b5]">
                      <span className="text-xs font-mono uppercase tracking-wider">
                        <span style={{ color: paper.accent }}>
                          {s.score !== undefined ? `得分：${s.score}/100` : '得分：待生成'}
                        </span>
                      </span>
                      {s.status === 'approved' && (
                        <Link
                          to={s.newspaper_slug ? `/newspaper/${s.newspaper_slug}` : '/'}
                          className="text-xs font-medium text-[#d4652f] hover:underline"
                        >
                          查看报纸（次日07:00后） →
                        </Link>
                      )}
                      {s.status === 'rejected' && (
                        <Link
                          to="/rejections"
                          className="text-xs font-medium text-[#9c8b75] hover:underline"
                        >
                          查看退稿信 →
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
