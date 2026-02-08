import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

export function ClaimBotPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bot, setBot] = useState<any>(null);

  const claimCode = searchParams.get('code');

  useEffect(() => {
    if (claimCode) {
      // 可以先查询机器人信息
      fetchBotInfo();
    }
  }, [claimCode]);

  const fetchBotInfo = async () => {
    // TODO: 实现查询机器人信息
  };

  const handleFeishuLogin = () => {
    // 构造飞书 OAuth URL
    const feishuAppId = import.meta.env.VITE_FEISHU_APP_ID;
    const redirectUri = `${window.location.origin}/oauth/feishu/callback`;
    const state = JSON.stringify({ claimCode, returnUrl: window.location.pathname });
    
    const oauthUrl = `https://open.feishu.cn/open-apis/authen/v1/authorize?app_id=${feishuAppId}&redirect_uri=${encodeURIComponent(
      redirectUri
    )}&state=${encodeURIComponent(state)}`;

    window.location.href = oauthUrl;
  };

  const handleClaim = async () => {
    if (!claimCode) {
      setError('缺少认领码');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 这里应该先进行飞书登录，获取 code
      // 然后调用认领接口
      handleFeishuLogin();
    } catch (err: any) {
      setError(err.response?.data?.detail || '认领失败');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <span className="text-white text-4xl">🤖</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
          认领机器人
        </h1>
        <p className="text-center text-gray-600 mb-8">
          通过飞书验证身份，认领你的机器人
        </p>

        {/* Bot Info (if available) */}
        {bot && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              {bot.avatar_url ? (
                <img
                  src={bot.avatar_url}
                  alt={bot.bot_name}
                  className="w-12 h-12 rounded-full"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xl font-bold">
                  {bot.bot_name[0]}
                </div>
              )}
              <div>
                <h3 className="font-semibold text-gray-900">{bot.bot_name}</h3>
                <p className="text-sm text-gray-500">{bot.bot_id}</p>
              </div>
            </div>
            {bot.description && (
              <p className="mt-3 text-sm text-gray-700">{bot.description}</p>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Action */}
        {claimCode ? (
          <>
            <button
              onClick={handleClaim}
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin h-5 w-5"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>处理中...</span>
                </>
              ) : (
                <>
                  <img
                    src="/feishu-logo.svg"
                    alt="Feishu"
                    className="w-5 h-5"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <span>使用飞书认领</span>
                </>
              )}
            </button>

            <p className="mt-4 text-xs text-center text-gray-500">
              点击后将跳转到飞书进行身份验证
            </p>
          </>
        ) : (
          <div className="text-center">
            <p className="text-red-600 mb-4">缺少认领码</p>
            <button
              onClick={() => navigate('/')}
              className="text-blue-600 hover:underline"
            >
              返回首页
            </button>
          </div>
        )}

        {/* Help */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-2">认领流程：</h3>
          <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
            <li>点击"使用飞书认领"按钮</li>
            <li>在飞书页面完成身份验证</li>
            <li>系统验证你与机器人的关系</li>
            <li>所有者直接认领，非所有者需等待批准</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
