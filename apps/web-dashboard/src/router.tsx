import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import { PageWrapper } from "./components/layout/PageWrapper";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <PageWrapper>
        <App />
      </PageWrapper>
    ),
  },
  {
    path: "/cves",
    element: (
      <PageWrapper>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold">CVE Explorer</h1>
          <p className="text-muted-foreground">Monitor and analyze vulnerability propagation across ecosystems.</p>
        </div>
      </PageWrapper>
    ),
  },
  {
    path: "/packages",
    element: (
      <PageWrapper>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold">Package Insights</h1>
          <p className="text-muted-foreground">Deep dive into affected package versions and dependency trees.</p>
        </div>
      </PageWrapper>
    ),
  },
  {
    path: "/repos",
    element: (
      <PageWrapper>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold">Monitored Repositories</h1>
          <p className="text-muted-foreground">Manage the open-source projects you are tracking for propagation.</p>
        </div>
      </PageWrapper>
    ),
  },
  {
    path: "/notifications",
    element: (
      <PageWrapper>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold">Alert Notifications</h1>
          <p className="text-muted-foreground">Recent security alerts and propagation events needing attention.</p>
        </div>
      </PageWrapper>
    ),
  },
]);

export const Router = () => <RouterProvider router={router} />;
