import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Link from 'next/link';
import Head from 'next/head';
import { userAPI } from '@/lib/api';
import { useRouter } from 'next/router';
import { getErrorMessage } from '@/lib/errorHandler';

export default function BiometricEnroll() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
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

      // Check if at least one video input device exists
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

      // Provide specific error messages based on error type
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Camera permission denied. Please allow camera access in your browser settings and try again.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No camera found. Please connect a camera and try again.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setError('Camera is already in use by another application. Please close other apps using the camera and try again.');
      } else if (err.name === 'OverconstrainedError') {
        setError('Camera does not support the required video format. Trying with default settings...');
        // Retry with minimal constraints
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

  const handleEnroll = async () => {
    if (!capturedImage) {
      setError('Please capture an image first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const base64Data = capturedImage.split(',')[1];
      await userAPI.enrollBiometric({
        biometric_data: base64Data,
        biometric_type: 'face',
      });

      setSuccess('Biometric enrollment successful!');
      await refreshUser();

      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to enroll biometric data'));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete your biometric enrollment?')) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      await userAPI.deleteBiometric();
      setSuccess('Biometric data deleted successfully');
      await refreshUser();

      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to delete biometric data'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Biometric Enrollment - DigiLocker 2.0</title>
      </Head>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/dashboard" className="text-sm text-primary-600 hover:text-primary-700">
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Biometric Enrollment</h1>
          <p className="text-gray-600 mb-6">
            {user?.biometric_enrolled
              ? 'Manage your biometric authentication'
              : 'Set up face recognition for secure login'}
          </p>

          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-4 rounded-md bg-green-50 p-4">
              <div className="text-sm text-green-800">{success}</div>
            </div>
          )}

          {user?.biometric_enrolled ? (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-green-800">Biometric authentication is enabled</h3>
                    <p className="mt-2 text-sm text-green-700">
                      You can now use face recognition to log in to your account.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <button
                  onClick={handleDelete}
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  {loading ? 'Deleting...' : 'Delete Biometric Data'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
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
                        <li>Position your face in the center of the camera frame</li>
                        <li>Ensure good lighting and remove any obstructions</li>
                        <li>Look directly at the camera</li>
                        <li>Click capture when ready</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Camera/Image Preview */}
              <div className="flex justify-center">
                <div className="relative bg-gray-100 rounded-lg overflow-hidden" style={{ width: 640, height: 480 }}>
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
                      onClick={handleEnroll}
                      disabled={loading}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm font-medium disabled:opacity-50"
                    >
                      {loading ? 'Enrolling...' : 'Enroll Biometric'}
                    </button>
                  </>
                )}
              </div>

              {/* Security Info */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Privacy & Security</h3>
                <div className="text-sm text-gray-700 space-y-1">
                  <p>• Your biometric data is encrypted and stored securely</p>
                  <p>• Face embeddings are hashed using SHA-256</p>
                  <p>• Biometric data is never shared with third parties</p>
                  <p>• You can delete your biometric data at any time</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
