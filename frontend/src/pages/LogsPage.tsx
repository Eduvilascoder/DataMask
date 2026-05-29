import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import LogTable from '../components/LogTable';
import es from '../i18n/es';

const LogsPage: React.FC = () => {
  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header variant="h1" description={es.logs.description}>
            {es.logs.title}
          </Header>
        }
      >
        <LogTable />
      </Container>
    </SpaceBetween>
  );
};

export default LogsPage;
