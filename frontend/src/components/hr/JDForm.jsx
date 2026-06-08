import { useState } from 'react';
import './JDForm.css';

export default function JDForm({ onSubmit, loading }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [department, setDepartment] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;
    onSubmit({ title: title.trim(), description: description.trim(), department: department.trim() || null });
    setTitle('');
    setDescription('');
    setDepartment('');
  };

  return (
    <form className="jd-form glass" onSubmit={handleSubmit} id="jd-create-form">
      <h3 className="jd-form__title">Create New Job Description</h3>

      <div className="jd-form__field">
        <label htmlFor="jd-title">Job Title</label>
        <input
          id="jd-title"
          className="input"
          type="text"
          placeholder="e.g. Senior Software Engineer"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div className="jd-form__field">
        <label htmlFor="jd-department">Department (optional)</label>
        <input
          id="jd-department"
          className="input"
          type="text"
          placeholder="e.g. Engineering, Marketing"
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
        />
      </div>

      <div className="jd-form__field">
        <label htmlFor="jd-description">Job Description</label>
        <textarea
          id="jd-description"
          className="input jd-form__textarea"
          placeholder="Paste the full job description here..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={8}
        />
      </div>

      <button
        type="submit"
        className="btn btn-primary jd-form__submit"
        disabled={loading || !title.trim() || !description.trim()}
        id="jd-submit-btn"
      >
        {loading ? (
          <>
            <span className="spinner" /> Creating...
          </>
        ) : (
          '+ Create Job Description'
        )}
      </button>
    </form>
  );
}
