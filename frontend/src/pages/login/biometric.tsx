import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import Head from 'next/head';
import { authAPI } from '@/lib/api';
import { useRouter } from 'next/router';
import { getErrorMessage } from '@/lib/errorHandler';

export default function BiometricLogin() {
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraAvailable, setCameraAvailable] = useState<boolean | null>(null);

  // Check if camera is available on mount
  useEffect(() => {
    checkCameraAvailability();
  }, []);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  const checkCameraAvailability = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setCameraAvailable(false);
        setError('Camera API is not supported in your browser. Please use a modern browser like Chrome, Firefox, or Safari.');
        return;
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      const hasCamera = devices.some(device => device.kind === 'videoinput');
      setCameraAvailable(hasCamera);

      if (!hasCamera) {
        setError('No camera detected. Please connect a camera and refresh the page.');
      }
    } catch (err) {
      console.error('Error checking camera availability:', err);
      setCameraAvailable(false);
      setError('Unable to detect camera. Please check your browser permissions.');
    }
  };

  const startCamera = async () => {
    try {
      setLoading(true);
      setError('');

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false,
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setCameraActive(true);
      setLoading(false);
    } catch (err: any) {
      setLoading(false);
      console.error('Camera error:', err);

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Camera permission denied. Please allow camera access in your browser settings and try again.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No camera found. Please connect a camera and try again.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('Camera is already in use by another application. Please close other apps using the camera and try again.');
      } else if (err.name === 'OverconstrainedError') {
        setError('Camera does not support the required video format. Trying with default settings...');
        try {
          const mediaStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false,
          });
          setStream(mediaStream);
          if (videoRef.current) {
            videoRef.current.srcObject = mediaStream;
          }
          setCameraActive(true);
          setError('');
        } catch (retryErr) {
          setError('Failed to access camera even with default settings.');
        }
      } else if (err.name === 'TypeError') {
        setError('Camera API is not supported. Please ensure you are using HTTPS or localhost.');
      } else {
        setError(`Failed to access camera: ${err.message || 'Unknown error'}`);
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.9);
        setCapturedImage(imageData);
        stopCamera();
      }
    }
  };

  const retakeImage = () => {
    setCapturedImage(null);
    startCamera();
  };

  const handleLogin = async () => {
    if (!username.trim()) {
      setError('Please enter your username');
      return;
    }

    if (!capturedImage) {
      setError('Please capture your face image');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const base64Data = capturedImage.split(',')[1];
      const response = await authAPI.loginBiometric({
        username: username.trim(),
        biometric_data: base64Data,
      });

      // Store tokens
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err: any) {
      setError(getErrorMessage(err, 'Biometric login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Biometric Login - DigiLocker 2.0</title>
      </Head>
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Login with Biometric
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Or{' '}
              <Link href="/login" className="font-medium text-primary-600 hover:text-primary-500">
                login with password
              </Link>
            </p>
          </div>

          <div className="bg-white shadow-lg rounded-lg p-6 space-y-6">
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            )}

            {/* Username Input */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Instructions</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <ul className="list-disc pl-5 space-y-1">
                      <li>Enter your username above</li>
                      <li>Position your face in the center of the camera frame</li>
                      <li>Ensure good lighting and remove any obstructions</li>
                      <li>Look directly at the camera and click capture</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Camera/Image Preview */}
            <div className="flex justify-center">
              <div className="relative bg-gray-100 rounded-lg overflow-hidden" style={{ width: 640, maxWidth: '100%', height: 480 }}>
                {!capturedImage ? (
                  <>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      className="w-full h-full object-cover"
                      style={{ display: cameraActive ? 'block' : 'none' }}
                    />
                    {!cameraActive && (
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                        <div className="text-center p-4">
                          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <p className="mt-2 text-sm text-gray-300">
                            {cameraAvailable === null ? 'Checking camera...' :
                             cameraAvailable === false ? 'No camera detected' :
                             'Click "Start Camera" below'}
                          </p>
                          {cameraAvailable === false && (
                            <button
                              onClick={checkCameraAvailability}
                              className="mt-3 text-xs text-primary-400 hover:text-primary-300 underline"
                            >
                              Refresh camera check
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <img src={capturedImage} alt="Captured" className="w-full h-full object-cover" />
                )}
              </div>
              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>

            {/* Camera Controls */}
            <div className="flex space-x-4">
              {!cameraActive && !capturedImage && (
                <button
                  onClick={startCamera}
                  disabled={loading || cameraAvailable === false}
                  className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Starting...' : 'Start Camera'}
                </button>
              )}
              {cameraActive && !capturedImage && (
                <>
                  <button
                    onClick={captureImage}
                    className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 text-sm font-medium"
                  >
                    Capture Image
                  </button>
                  <button
                    onClick={stopCamera}
                    className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 text-sm font-medium"
                  >
                    Cancel
                  </button>
                </>
              )}
              {capturedImage && (
                <>
                  <button
                    onClick={retakeImage}
                    className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 text-sm font-medium"
                  >
                    Retake
                  </button>
                  <button
                    onClick={handleLogin}
                    disabled={loading}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm font-medium disabled:opacity-50"
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </button>
                </>
              )}
            </div>

            {/* Security Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Privacy & Security</h3>
              <div className="text-sm text-gray-700 space-y-1">
                <p>• Your biometric data is encrypted during transmission</p>
                <p>• Face recognition uses secure post-quantum cryptography</p>
                <p>• Biometric data is never shared with third parties</p>
                <p>• Login attempts are logged for security audit</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
