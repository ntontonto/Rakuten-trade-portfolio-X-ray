import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SplashScreen from '../components/layout/SplashScreen';

describe('SplashScreen', () => {
  it('invokes onFilesSelected when files are chosen', async () => {
    const handleFiles = vi.fn();
    const { container } = render(<SplashScreen onFilesSelected={handleFiles} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });

    // Simulate selecting a file
    await userEvent.upload(input, file);

    expect(handleFiles).toHaveBeenCalledTimes(1);
    expect(handleFiles.mock.calls[0][0]).toBeInstanceOf(FileList);
    expect(handleFiles.mock.calls[0][0][0].name).toBe('test.csv');
  });

  it('supports drag and drop uploads', () => {
    const handleFiles = vi.fn();
    render(<SplashScreen onFilesSelected={handleFiles} />);

    const dropZone = screen.getByText(/ファイルを選択/i).closest('div')!;
    const file = new File(['content'], 'drag.csv', { type: 'text/csv' });

    fireEvent.dragEnter(dropZone, { dataTransfer: { files: [file] } });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });

    expect(handleFiles).toHaveBeenCalledTimes(1);
    expect(handleFiles.mock.calls[0][0][0].name).toBe('drag.csv');
  });
});
