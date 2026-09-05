import { Button, Layout } from 'antd'
import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { FileTextOutlined, MessageOutlined } from '@ant-design/icons'
import ConversationList from '../components/sidebar/ConversationList'
import ModelSelector from '../components/common/ModelSelector'
import { useAuthStore } from '../stores/authStore'

const { Sider, Content, Header } = Layout

export default function ChatLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const isDocuments = location.pathname === '/documents'

  // 路由守卫：未登录重定向到登录页
  if (!token) return <Navigate to="/login" replace />

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={260} theme="light">
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: 16, fontWeight: 600, fontSize: 16 }}>ChatBot</div>
          <div style={{ padding: '0 12px 8px' }}>
            <ModelSelector />
          </div>
          <ConversationList />
          <div style={{ padding: 12, borderTop: '1px solid #f0f0f0', display: 'flex', gap: 8 }}>
            <Button
              block
              type={isDocuments ? 'default' : 'primary'}
              ghost={isDocuments}
              icon={<MessageOutlined />}
              onClick={() => navigate('/chat')}
            >
              对话
            </Button>
            <Button
              block
              type={isDocuments ? 'primary' : 'default'}
              icon={<FileTextOutlined />}
              onClick={() => navigate('/documents')}
            >
              文档管理
            </Button>
          </div>
        </div>
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 12,
          }}
        >
          <span style={{ color: '#666' }}>{user?.username}</span>
          <Button size="small" onClick={handleLogout}>
            退出登录
          </Button>
        </Header>
        <Content style={{ padding: 16, overflow: 'auto' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
