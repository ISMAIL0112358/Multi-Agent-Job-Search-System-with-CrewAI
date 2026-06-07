import './Loader.css';

export default function Loader({ message = 'Processing...', submessage = '' }) {
  return (
    <div className="loader-container" id="loader">
      <div className="loader-spinner">
        <div className="loader-ring" />
        <div className="loader-ring" />
        <div className="loader-ring" />
      </div>
      <p className="loader-message">{message}</p>
      {submessage && <p className="loader-submessage">{submessage}</p>}
    </div>
  );
}
