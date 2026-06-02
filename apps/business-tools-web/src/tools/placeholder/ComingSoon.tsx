type ComingSoonProps = {
  title: string;
};

export function ComingSoon({ title }: ComingSoonProps) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      <p>This tool slot is ready for the next workflow.</p>
    </div>
  );
}
