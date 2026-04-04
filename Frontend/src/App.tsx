import { ConfigProvider, theme } from 'antd'
import { useState } from 'react'
import { isLoggedIn, isStaff, logout } from './api'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TopicDetailPage from './pages/TopicDetailPage'
import SourcesPage from './pages/SourcesPage'

function App() {
  const [isDark, setIsDark] = useState(true)
  const [page, setPage] = useState<'login' | 'dashboard' | 'topic' | 'sources'>(
    isLoggedIn() ? 'dashboard' : 'login'
  )
  const [selectedTopicId, setSelectedTopicId] = useState<number>(0)

  const themeProps = {
    isDark,
    onToggleTheme: () => setIsDark(!isDark),
  }

  const openTopic = (topicId: number) => {
    setSelectedTopicId(topicId)
    setPage('topic')
  }

  const handleLogout = async () => {
    await logout()
    setPage('login')
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#8b5cf6',
          borderRadius: 12,
        },
      }}
    >
      {page === 'login' && (
        <LoginPage {...themeProps} onSuccess={() => setPage('dashboard')} />
      )}
      {page === 'dashboard' && (
        <DashboardPage
          {...themeProps}
          onSelectTopic={openTopic}
          onOpenSources={isStaff() ? () => setPage('sources') : undefined}
          onLogout={handleLogout}
        />
      )}
      {page === 'topic' && (
        <TopicDetailPage
          {...themeProps}
          topicId={selectedTopicId}
          onBack={() => setPage('dashboard')}
        />
      )}
      {page === 'sources' && (
        <SourcesPage
          {...themeProps}
          onBack={() => setPage('dashboard')}
        />
      )}
    </ConfigProvider>
  )
}

export default App
