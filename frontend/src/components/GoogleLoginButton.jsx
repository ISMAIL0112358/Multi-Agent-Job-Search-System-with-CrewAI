import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './GoogleLoginButton.css';

export default function GoogleLoginButton({ role = 'job_seeker', label, className = '' }) {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse) => {
    try {
      // credentialResponse.credential IS the signed Google OpenID Connect ID Token (JWT)
      const idToken = credentialResponse.credential;
      if (!idToken) {
        console.error('No ID token received from Google.');
        return;
      }

      const userData = await login({
        id_token: idToken,
        role: role,
      });

      if (userData.role === 'hr') {
        navigate('/hr');
      } else {
        navigate('/');
      }
    } catch (err) {
      console.error('Google ID Token authentication failed:', err);
    }
  };

  return (
    <div className={`google-login-container ${className}`} id={`google-login-${role}`}>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => console.error('Google Sign In Failed')}
        theme="filled_black"
        shape="pill"
        size="large"
        text="signin_with"
        logo_alignment="left"
        width="260"
      />
    </div>
  );
}
