import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { PageWrapper } from "./components/layout/PageWrapper";
import DashboardPage from "./pages/DashboardPage";
import CveListPage from "./pages/CveListPage";
import NotificationsPage from "./pages/NotificationsPage";
import OptOutPage from "./pages/OptOutPage";
import RemediationPage from "./pages/RemediationPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <PageWrapper>
        <DashboardPage />
      </PageWrapper>
    ),
  },
  {
    path: "/cves",
    element: (
      <PageWrapper>
        <CveListPage />
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
        <NotificationsPage />
      </PageWrapper>
    ),
  },
  {
    path: "/opt-out",
    element: (
      <PageWrapper>
        <OptOutPage />
      </PageWrapper>
    ),
  },
  {
    path: "/remediation",
    element: (
      <PageWrapper>
        <RemediationPage />
      </PageWrapper>
    ),
  },
]);

export const Router = () => <RouterProvider router={router} />;
