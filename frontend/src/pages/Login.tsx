import { Button, Card, Form, Input, message } from 'antd'
import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { login, register } from '../services/authApi'
import { useAuthStore } from '../stores/authStore'

type LoginMode = 'login' | 'register'

interface FormValues {
  username: string
  password: string
  confirm?: string
}

export default function Login() {
  const [mode, setMode] = useState<LoginMode>('login')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)

  // 已登录直接进聊天页
  if (token) return <Navigate to="/chat" replace />

  const onFinish = async (values: FormValues) => {
    setLoading(true)
    try {
      const data =
        mode === 'login'
          ? await login(values.username, values.password)
          : await register(values.username, values.password)
      useAuthStore.getState().setAuth(data.access_token, data.user)
      message.success(mode === 'login' ? '登录成功' : '注册成功')
      navigate('/chat', { replace: true })
    } catch (err) {
      const code = (err as { response?: { data?: { code?: string; message?: string } } })
        .response?.data?.code
      if (code === 'USERNAME_EXISTS') {
        message.error('用户名已被占用')
      } else if (code === 'INVALID_CREDENTIALS') {
        message.error('用户名或密码错误')
      } else {
        message.error('请求失败，请稍后重试')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#f5f5f5',
      }}
    >
      <Card title="ChatBot" style={{ width: 380 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <Button
            block
            type={mode === 'login' ? 'primary' : 'default'}
            onClick={() => setMode('login')}
          >
            登录
          </Button>
          <Button
            block
            type={mode === 'register' ? 'primary' : 'default'}
            onClick={() => setMode('register')}
          >
            注册
          </Button>
        </div>
        <Form onFinish={onFinish} layout="vertical" key={mode}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input placeholder="用户名" size="large" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              ...(mode === 'register' ? [{ min: 6, message: '密码至少 6 位' }] : []),
            ]}
          >
            <Input.Password placeholder="密码" size="large" />
          </Form.Item>
          {mode === 'register' && (
            <Form.Item
              name="confirm"
              dependencies={['password']}
              rules={[
                { required: true, message: '请再次输入密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password placeholder="确认密码" size="large" />
            </Form.Item>
          )}
          <Button type="primary" htmlType="submit" block size="large" loading={loading}>
            {mode === 'login' ? '登录' : '注册'}
          </Button>
        </Form>
      </Card>
    </div>
  )
}
