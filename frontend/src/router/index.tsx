import { Navigate, createBrowserRouter } from 'react-router-dom'
import ChatLayout from '../layouts/ChatLayout'
import Chat from '../pages/Chat'
import Documents from '../pages/Documents'
import Login from '../pages/Login'

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: <ChatLayout />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: 'chat', element: <Chat /> },
      { path: 'documents', element: <Documents /> },
    ],
  },
])
