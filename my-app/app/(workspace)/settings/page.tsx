import { redirect } from "next/navigation";

// Redirect /settings directly to the GitHub integration page as the default
export default function SettingsPage() {
  redirect("/settings/integrations/github");
}
