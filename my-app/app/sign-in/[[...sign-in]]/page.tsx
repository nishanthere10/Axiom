import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background">
      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto",
            cardBox: "shadow-xl border border-border/50 rounded-xl",
            card: "bg-card",
            headerTitle: "text-foreground",
            headerSubtitle: "text-muted-foreground",
            socialButtonsBlockButton:
              "bg-secondary text-foreground border-border hover:bg-secondary/80",
            formFieldLabel: "text-foreground",
            formFieldInput:
              "bg-background border-border text-foreground focus:ring-primary",
            formButtonPrimary:
              "bg-primary hover:bg-primary/90 text-primary-foreground",
            footerActionLink: "text-primary hover:text-primary/80",
            identityPreviewEditButton: "text-primary",
          },
        }}
      />
    </div>
  );
}
