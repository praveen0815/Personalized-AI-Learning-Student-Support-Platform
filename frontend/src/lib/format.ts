export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function greetingForHour(hour: number, name: string): string {
  if (hour < 12) {
    return `Good morning, ${name}`;
  }
  if (hour < 17) {
    return `Good afternoon, ${name}`;
  }
  return `Good evening, ${name}`;
}
