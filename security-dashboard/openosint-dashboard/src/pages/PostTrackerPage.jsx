import PostTracker from '../components/PostTracker.jsx'

export default function PostTrackerPage() {
  return (
    <div>
      <h2 className="page-title">Post Tracker</h2>
      <p className="section-kicker" style={{ marginBottom: 20 }}>
        Find who else posted a cybersecurity story, then review timing and engagement.
      </p>
      <div className="panel panel-body">
        <PostTracker />
      </div>
    </div>
  )
}
